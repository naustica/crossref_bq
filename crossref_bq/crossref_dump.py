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

# Modifications copyright (C) 2021 Nick Haupka


import logging
import requests
import os
import shutil
import functools
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
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
                    r.raw.read = functools.partial(r.raw.read,
                                                   decode_content=True)
                    shutil.copyfileobj(r.raw, file)

    def extract(self) -> None:

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
    def transform_file(input_file_path: str, output_file_path: str) -> bool:

        cmd = 'mawk \'BEGIN {FS="\\":";RS=",\\"";OFS=FS;ORS=RS} {for (i=1; i<=NF;i++) if(i != NF) gsub("-", "_", $i)}1\'' \
              f' {input_file_path} | ' \
              'mawk \'!/^\}$|^\]$|,\\"$/{gsub("\[\[", "[");gsub("]]", "]");gsub(/,[ \\t]*$/,"");' \
              'gsub("\\"timestamp\\":_", "\\"timestamp\\":");gsub("\\"date_parts\\":\[null]", "\\"date_parts\\":[]");' \
              'gsub(/^\{\\"items\\":\[/,"");print}\' > ' \
              f'{output_file_path}'

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='/bin/bash')

        stdout, stderr = p.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        logging.debug(stdout)
        success = p.returncode == 0

        if success:
            logging.info(f'Transform file success: {input_file_path}')
        else:
            logging.error(f'Transform file error: {input_file_path}')
            logging.error(stderr)

        return success

    def transform_release(self, max_workers: int = cpu_count()) -> bool:

        output_release_path = self.transform_path

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            futures_msgs = {}

            for input_file in os.listdir(self.extract_path):
                output_file_path = os.path.join(output_release_path, os.path.basename(input_file) + 'l')
                msg = f'input_file_path={input_file}, output_file_path={output_file_path}'
                logging.info(f'transform_release: {msg}')
                future = executor.submit(CrossrefSnapshot.transform_file,
                                         input_file_path=self.extract_path + '/' + input_file,
                                         output_file_path=output_file_path)
                futures.append(future)
                futures_msgs[future] = msg

            results = []
            for future in as_completed(futures):
                success = future.result()
                msg = futures_msgs[future]
                results.append(success)
                if success:
                    logging.info(f'transform_release success: {msg}')
                else:
                    logging.error(f'transform_release failed: {msg}')

        return all(results)
