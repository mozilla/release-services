# -*- coding: utf-8 -*-
import concurrent.futures
import os
import sqlite3
import tarfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import requests

from cli_common.log import get_logger
from shipit_code_coverage import grcov
from shipit_code_coverage import taskcluster

logger = get_logger(__name__)


PLATFORMS = ['linux', 'windows']
IGNORED_SUITE_PREFIXES = ['awsy', 'talos', 'test-coverage', 'test-coverage-wpt']
# TODO: Calculate this dinamically when https://github.com/klahnakoski/ActiveData-ETL/issues/40 is fixed.
TEST_COVERAGE_SUITES = ['reftest', 'web-platform', 'mochitest', 'xpcshell', 'jsreftest', 'crashtest']


def get_suites(revision):
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
        'limit': 500000,
        'groupby': ['run.suite']
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
            {'eq': {'run.suite': suite}},
            {'prefix': {'run.key': run_key_prefix}},
        ]},
        'limit': 50000,
        'select': ['result.test', 'run.key']
    })

    return r.json()['data']


def group_by_20k(data):
    groups = defaultdict(list)
    total_count = 0

    for elem, count in data:
        total_count += count
        groups[total_count // 20000].append(elem)

    return groups.values()


def get_test_coverage_suites():
    r = requests.post('https://activedata.allizom.org/query', json={
        'from': 'coverage',
        'where': {'and': [
            {'eq': {'repo.branch.name': 'mozilla-central'}},
            {'gte': {'repo.push.date': {'date': 'today-week'}}},
            {'gt': {'source.file.total_covered': 0}},
            {'exists': 'test.name'}
        ]},
        'limit': 50000,
        'select': {'aggregate': 'cardinality', 'value': 'test.name'},
        'groupby': ['test.suite']
    })

    return r.json()['data']


def get_test_coverage_tests(suites):
    r = requests.post('https://activedata.allizom.org/query', json={
        'from': 'coverage',
        'where': {'and': [
            {'eq': {'repo.branch.name': 'mozilla-central'}},
            {'gte': {'repo.push.date': {'date': 'today-week'}}},
            {'gt': {'source.file.total_covered': 0}},
            {'exists': 'test.name'},
            {'in': {'test.suite': suites}}
        ]},
        'limit': 50000,
        'select': {'aggregate': 'cardinality', 'value': 'source.file.name'},
        'groupby': ['test.name']
    })

    return r.json()['data']


def get_test_coverage_files(tests):
    r = requests.post('https://activedata.allizom.org/query', json={
        'from': 'coverage',
        'where': {'and': [
            {'eq': {'repo.branch.name': 'mozilla-central'}},
            {'gte': {'repo.push.date': {'date': 'today-week'}}},
            {'gt': {'source.file.total_covered': 0}},
            {'exists': 'test.name'},
            {'in': {'test.name': tests}}
        ]},
        'limit': 50000,
        'select': ['source.file.name', 'test.name']
    })

    return r.json()['data']


def is_chunk_only_suite(suite):
    # Ignore test-coverage, test-coverage-wpt, awsy and talos.
    if any(suite.startswith(prefix) for prefix in IGNORED_SUITE_PREFIXES):
        return False
    # Ignore suites supported by test-coverage.
    if any(test_coverage_suite in suite for test_coverage_suite in TEST_COVERAGE_SUITES):
        return False
    return True


def generate(repo_dir, revision, artifactsHandler, out_dir='.'):
    sqlite_file = os.path.join(out_dir, 'chunk_mapping.sqlite')
    tarxz_file = os.path.join(out_dir, 'chunk_mapping.tar.xz')

    with sqlite3.connect(sqlite_file) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE file_to_chunk (path text, platform text, chunk text)')
        c.execute('CREATE TABLE chunk_to_test (platform text, chunk text, path text)')
        c.execute('CREATE TABLE file_to_test (source text, test text)')

        test_coverage_suites = get_test_coverage_suites()
        for suites in group_by_20k(test_coverage_suites):
            test_coverage_tests = get_test_coverage_tests(suites)
            for tests in group_by_20k(test_coverage_tests):
                tests_files_data = get_test_coverage_files(tests)

                source_names = tests_files_data['source.file.name']
                test_iter = enumerate(tests_files_data['test.name'])
                source_test_iter = ((source_names[i], test) for i, test in test_iter)

                c.executemany('INSERT INTO file_to_test VALUES (?,?)', source_test_iter)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for platform in PLATFORMS:
                for chunk in artifactsHandler.get_chunks():
                    suite = taskcluster.get_suite(chunk)
                    if not is_chunk_only_suite(suite):
                        continue

                    future = executor.submit(grcov.files_list, artifactsHandler.get(platform=platform, chunk=chunk), source_dir=repo_dir)
                    futures[future] = (platform, chunk)

                for suite in get_suites(revision):
                    if not is_chunk_only_suite(suite):
                        continue

                    tests_data = get_tests_chunks(revision, platform, suite)
                    if len(tests_data) == 0:
                        continue

                    task_names = tests_data['run.key']
                    test_iter = enumerate(tests_data['result.test'])
                    chunk_test_iter = ((platform, taskcluster.get_chunk(task_names[i]), test) for i, test in test_iter)
                    c.executemany('INSERT INTO chunk_to_test VALUES (?,?,?)', chunk_test_iter)

            for future in concurrent.futures.as_completed(futures):
                (platform, chunk) = futures[future]
                files = future.result()
                c.executemany('INSERT INTO file_to_chunk VALUES (?,?,?)', ((f, platform, chunk) for f in files))

    with tarfile.open(tarxz_file, 'w:xz') as tar:
        tar.add(sqlite_file, os.path.basename(sqlite_file))
