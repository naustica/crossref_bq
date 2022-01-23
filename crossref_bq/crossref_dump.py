# Copyright 2020 Curtin University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Author: Aniek Roelofs, James Diprose

# Modifications copyright (C) 2022 Nick Haupka


import logging
import requests
import os
import ujson
import jsonlines
import shutil
import functools
import subprocess
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


class CrossrefSnapshot:

    def __init__(self,
                 year: int,
                 month: int,
                 filename: str = None,
                 download_path: str = None,
                 extract_path: str = None,
                 transform_path: str = None) -> None:
        self.year = year
        self.month = month
        self.url = 'https://api.crossref.org/snapshots/monthly/{year}/{month:02d}/all.json.tar.gz'.format(year=year,
                                                                                                          month=month)
        if not filename:
            self.filename = '{year}_{month:02d}.json.tar.gz'.format(year=year, month=month)
        else:
            self.filename = filename

        if not download_path:
            self.download_path = os.path.join(os.getcwd(), 'crossref_snapshots')
        else:
            self.download_path = download_path

        if not extract_path:
            self.extract_path = os.path.join(self.download_path, 'extract')
        else:
            self.extract_path = extract_path

        if not transform_path:
            self.transform_path = os.path.join(self.download_path, 'transform')
        else:
            self.transform_path = transform_path

        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.extract_path, exist_ok=True)
        os.makedirs(self.transform_path, exist_ok=True)

    def exists(self) -> bool:
        r = requests.head(self.url)

        if r.status_code == 302:
            return True
        else:
            return False

    def download(self) -> None:
        if self.exists():
            api_token = os.environ.get('CROSSREF_PLUS_API_TOKEN')
            if not api_token:
                raise ValueError('Missing API token.')

            header = {'Crossref-Plus-API-Token': f'Bearer {api_token}'}

            with requests.get(self.url, headers=header, stream=True) as r:
                if r.status_code != 200:
                    raise ConnectionError(f'Error downloading snapshot (status code={r.status_code})')

                with open(self.download_path + '/' + self.filename, 'wb') as file:
                    r.raw.read = functools.partial(r.raw.read, decode_content=True)
                    shutil.copyfileobj(r.raw, file)

    def extract(self):

        # mac
        # cmd = f'tar -xvf {self.download_path}/{self.filename} -C {self.extract_path}'

        # linux
        cmd = f'tar -xvf {self.download_path}/{self.filename} -C {self.extract_path} --use-compress-program=pigz'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='/bin/bash')
        stdout, stderr = p.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        logging.debug(stdout)

        success = p.returncode == 0 and 'error' not in stderr.lower()

        if success:
            logging.info(f'Extract snapshot success: {self.download_path}')
        else:
            logging.error(f'Extract snapshot error: {self.download_path}')
            logging.error(stdout)
            logging.error(stderr)

        return success

    @staticmethod
    def transform_file(input_file_path: str, output_file_path: str):

        with open(input_file_path, mode='r') as input_file:
            input_data = ujson.load(input_file)

        output_data = []
        for item in input_data['items']:
            output_data.append(CrossrefSnapshot.transform_item(item))

        with jsonlines.open(output_file_path, mode='w', compact=True) as output_file:
            output_file.write_all(output_data)

    @staticmethod
    def transform_item(item):

        if isinstance(item, dict):
            new = {}
            for k, v in item.items():

                if k == 'type':
                    if v != 'journal-article':
                        continue

                if k == 'DOI':
                    k = 'doi'

                if k == 'title':
                    if isinstance(v, list) and len(v) >= 1:
                        v = v[0]

                if k == 'container-title':
                    if isinstance(v, list) and len(v) >= 1:
                        v = v[0]

                if k == 'ISSN':
                    k = 'issn'
                    v = ','.join(list(set(v)))

                if k == 'archive':
                    v = ','.join(list(set(v)))

                if k in ['created',
                         'deposited',
                         'indexed',
                         'issued',
                         'posted',
                         'accepted',
                         'published-print',
                         'published-online',
                         'start']:

                    v = item[k].get('date-parts')

                    if not v:
                        continue

                    v = v[0]

                    if None in v:
                        continue

                    len_arr_date_parts = len(v)

                    if len_arr_date_parts > 0:
                        if not len(str(v[0])) == 4:
                            continue

                    if len_arr_date_parts == 1:
                        v = '-'.join([str(v[0]), '1', '1'])
                        v = datetime.strptime(v, '%Y-%m-%d')

                    elif len_arr_date_parts == 2:
                        v = '-'.join([str(v[0]), str(v[1]), '1'])
                        v = datetime.strptime(v, '%Y-%m-%d')

                    elif len_arr_date_parts == 3:
                        v = '-'.join([str(v[0]), str(v[1]), str(v[2])])
                        v = datetime.strptime(v, '%Y-%m-%d')

                    if k == 'issued':

                        filter_date = datetime(2013, 1, 1)

                        if not v >= filter_date:
                            continue

                    v = v.strftime('%Y-%m-%d')

                if k == 'date-parts':
                    continue

                k = k.replace('-', '_')

                new[k] = CrossrefSnapshot.transform_item(v)
            return new
        elif isinstance(item, list):
            return [CrossrefSnapshot.transform_item(i) for i in item]
        else:
            return item

    def transform_release(self, max_workers: int = cpu_count()):

        finished = 0

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for input_file in os.listdir(self.extract_path):
                output_file_path = os.path.join(self.transform_path, os.path.basename(input_file) + 'l')
                future = executor.submit(CrossrefSnapshot.transform_file,
                                         input_file_path=self.extract_path + '/' + input_file,
                                         output_file_path=output_file_path)
                futures.append(future)

            for future in as_completed(futures):
                future.result()
                finished += 1
                if finished % 1000 == 0:
                    logging.info(f"Transformed {finished} files")
