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
import os
import json
import jsonlines
import subprocess
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


filename='all.json.tar.gz'
download_path='/scratch/users/haupka'
extract_path='/scratch/users/haupka/extract'
transform_path='/scratch/users/haupka/transform'

os.makedirs(download_path, exist_ok=True)
os.makedirs(extract_path, exist_ok=True)
os.makedirs(transform_path, exist_ok=True)


def extract():

    # mac
    # cmd = f'tar -xvf {self.download_path}/{self.filename} -C {self.extract_path}'

    # linux
    cmd = f'tar -xvf {download_path}/{filename} -C {extract_path} --use-compress-program=pigz'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='/bin/bash')
    stdout, stderr = p.communicate()

    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')

    logging.debug(stdout)

    success = p.returncode == 0 and 'error' not in stderr.lower()

    if success:
        logging.info(f'Extract snapshot success: {download_path}')
    else:
        logging.error(f'Extract snapshot error: {download_path}')
        logging.error(stdout)
        logging.error(stderr)

    return success


def transform_file(input_file_path: str, output_file_path: str):

    with open(input_file_path, mode='r') as input_file:
        input_data = json.load(input_file)

    output_data = []
    for item in input_data['items']:

        transformed_item = transform_item(item)

        filtered_item = filter_item(transformed_item)

        if filtered_item:
            output_data.append(filtered_item)

    with jsonlines.open(output_file_path, mode='w', compact=True) as output_file:
        output_file.write_all(output_data)


def transform_item(item):

    if isinstance(item, dict):
        new = {}
        for k, v in item.items():

            if k == 'DOI':
                k = 'doi'

            if k == 'URL':
                k = 'url'

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
                    v = [[]]

                v = v[0]

                try:

                    len_arr_date_parts = len(v)

                    if len_arr_date_parts > 0:
                        if not len(str(v[0])) == 4:
                            v = None

                    if len_arr_date_parts == 1:
                        if v[0] is None:
                            v = None
                        else:
                            v = '-'.join([str(v[0]), '1', '1'])
                            v = datetime.strptime(v, '%Y-%m-%d')

                    elif len_arr_date_parts == 2:
                        v = '-'.join([str(v[0]), str(v[1]), '1'])
                        v = datetime.strptime(v, '%Y-%m-%d')

                    elif len_arr_date_parts == 3:
                        v = '-'.join([str(v[0]), str(v[1]), str(v[2])])
                        v = datetime.strptime(v, '%Y-%m-%d')

                except:

                    v = None

                if v:

                    v = v.strftime('%Y-%m-%d')

            k = k.replace('-', '_')

            new[k] = transform_item(v)
        return new
    elif isinstance(item, list):
        return [transform_item(i) for i in item]
    else:
        return item


def filter_item(item):

    if 'type' not in item.keys():
        return None

    if 'issued' not in item.keys():
        return None

    filter_status = True

    for k, v in item.items():
        if k == 'type' and v != 'journal-article':
            filter_status = False
        if k == 'issued':
            filter_date = datetime(2013, 1, 1)
            if v is None:
                filter_status = False
            if v is not None:
                if not datetime.strptime(v, '%Y-%m-%d') >= filter_date:
                    filter_status = False

    if filter_status:
        return item
    else:
        return None


def transform_release(max_workers: int = cpu_count()):

    finished = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for input_file in os.listdir(extract_path):
            output_file_path = os.path.join(transform_path, os.path.basename(input_file) + 'l')
            future = executor.submit(transform_file,
                                     input_file_path=extract_path + '/' + input_file,
                                     output_file_path=output_file_path)
            futures.append(future)

        for future in as_completed(futures):
            future.result()
            finished += 1
            if finished % 1000 == 0:
                logging.info(f"Transformed {finished} files")


extract()
transform_release()