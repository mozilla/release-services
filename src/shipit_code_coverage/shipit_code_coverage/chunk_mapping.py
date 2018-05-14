# -*- coding: utf-8 -*-
import concurrent.futures
import os
import sqlite3
import tarfile
from concurrent.futures import ThreadPoolExecutor

import requests

from cli_common.log import get_logger
from shipit_code_coverage import grcov
from shipit_code_coverage import taskcluster

logger = get_logger(__name__)


def generate(repo_dir, revision, artifactsHandler, out_dir='.'):
    sqlite_file = os.path.join(out_dir, 'chunk_mapping.sqlite')
    tarxz_file = os.path.join(out_dir, 'chunk_mapping.tar.xz')

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for platform in ['linux', 'windows']:
            for chunk in artifactsHandler.get_chunks():
                future = executor.submit(grcov.files_list, artifactsHandler.get(platform=platform, chunk=chunk), source_dir=repo_dir)
                futures[future] = (platform, chunk)

        with sqlite3.connect(sqlite_file) as conn:
            c = conn.cursor()
            c.execute('CREATE TABLE file_to_chunk (path text, platform text, chunk text)')
            c.execute('CREATE TABLE chunk_to_test (platform text, chunk text, path text)')

            for future in concurrent.futures.as_completed(futures):
                (platform, chunk) = futures[future]
                files = future.result()
                c.executemany('INSERT INTO file_to_chunk VALUES (?,?,?)', ((f, platform, chunk) for f in files))

            try:
                # Retrieve chunk -> tests mapping from ActiveData.
                r = requests.post('https://activedata.allizom.org/query', json={
                    'from': 'unittest',
                    'where': {'and': [
                        {'eq': {'repo.branch.name': 'mozilla-central'}},
                        {'eq': {'repo.changeset.id12': revision[:12]}},
                        {'or': [
                            {'prefix': {'run.key': 'test-linux64-ccov'}},
                            {'prefix': {'run.key': 'test-windows10-64-ccov'}}
                        ]}
                    ]},
                    'limit': 50000,
                    'select': ['result.test', 'run.key']
                })

                tests_data = r.json()['data']

                task_names = tests_data['run.key']
                test_iter = enumerate(tests_data['result.test'])
                chunk_test_iter = ((taskcluster.get_platform(task_names[i]), taskcluster.get_chunk(task_names[i]), test) for i, test in test_iter)
                c.executemany('INSERT INTO chunk_to_test VALUES (?,?,?)', chunk_test_iter)
            except KeyError:
                # ActiveData is failing too often, so we need to ignore the error here.
                logger.error('Failed to retrieve chunk to tests mapping from ActiveData.')

    with tarfile.open(tarxz_file, 'w:xz') as tar:
        tar.add(sqlite_file, os.path.basename(sqlite_file))
