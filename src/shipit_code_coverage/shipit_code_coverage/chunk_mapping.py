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


PLATFORMS = ['linux', 'windows']


def get_suites(revision):
    r = requests.post('https://activedata.allizom.org/query', json={
        "from":"unittest",
        "where":{"and":[
            {"eq":{"repo.branch.name":"mozilla-central"}},
            {"eq":{"repo.changeset.id12":revision[:12]}},
            {"or":[
                {"prefix":{"run.key":"test-linux64-ccov"}},
                {"prefix":{"run.key":"test-windows10-64-ccov"}}
            ]}
        ]},
        "limit":500000,
        "groupby":["run.suite"]
    })

    suites_data = r.json()['data']

    return [e[0] for e in suites_data]


# Retrieve chunk -> tests mapping from ActiveData.
def get_tests_chunks(revision, platform, suite):
    if platform == 'linux':
        run_key_prefix = 'test-linux64-ccov'
    elif platform == 'windows':
        run_key_prefix = 'test-windows10-64-ccov'

    r = requests.post('https://activedata.allizom.org/query', json={
        'from': 'unittest',
        'where': {'and': [
            {'eq': {'repo.branch.name': 'mozilla-central'}},
            {'eq': {'repo.changeset.id12': revision[:12]}},
            {"eq":{"run.suite": suite}},
            {'prefix': {'run.key': run_key_prefix}},
        ]},
        'limit': 50000,
        'select': ['result.test', 'run.key']
    })

    return r.json()['data']


def generate(repo_dir, revision, artifactsHandler, out_dir='.'):
    sqlite_file = os.path.join(out_dir, 'chunk_mapping.sqlite')
    tarxz_file = os.path.join(out_dir, 'chunk_mapping.tar.xz')

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for platform in PLATFORMS:
            for chunk in artifactsHandler.get_chunks():
                future = executor.submit(grcov.files_list, artifactsHandler.get(platform=platform, chunk=chunk))
                futures[future] = (platform, chunk)

        with sqlite3.connect(sqlite_file) as conn:
            c = conn.cursor()
            c.execute('CREATE TABLE file_to_chunk (path text, platform text, chunk text)')
            c.execute('CREATE TABLE chunk_to_test (platform text, chunk text, path text)')

            for future in concurrent.futures.as_completed(futures):
                (platform, chunk) = futures[future]
                files = future.result()
                c.executemany('INSERT INTO file_to_chunk VALUES (?,?,?)', ((f, platform, chunk) for f in files))

            for platform in PLATFORMS:
                for suite in get_suites(revision):
                    tests_data = get_tests_chunks(revision, platform, suite)
                    if len(tests_data) == 0:
                        continue

                    task_names = tests_data['run.key']
                    test_iter = enumerate(tests_data['result.test'])
                    chunk_test_iter = ((taskcluster.get_platform(task_names[i]), taskcluster.get_chunk(task_names[i]), test) for i, test in test_iter)
                    c.executemany('INSERT INTO chunk_to_test VALUES (?,?,?)', chunk_test_iter)

    with tarfile.open(tarxz_file, 'w:xz') as tar:
        tar.add(sqlite_file, os.path.basename(sqlite_file))
