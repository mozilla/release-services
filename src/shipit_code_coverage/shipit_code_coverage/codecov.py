# -*- coding: utf-8 -*-
import json
import os
import shutil
import tarfile
import requests
import hglib
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import sqlite3

from cli_common.log import get_logger
from cli_common.command import run_check
from cli_common.utils import mkdir, retry, ThreadPoolExecutorResult

from shipit_code_coverage import taskcluster, uploader
from shipit_code_coverage.artifacts import ArtifactsHandler
from shipit_code_coverage.github import GitHubUtils
from shipit_code_coverage.notifier import Notifier
from shipit_code_coverage.secrets import secrets


logger = get_logger(__name__)


class CodeCov(object):

    def __init__(self, revision, cache_root, client_id, access_token):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = [
            'cppunit', 'gtest', 'web-platform-tests', 'talos',
        ]

        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        self.client_id = client_id
        self.access_token = access_token

        self.githubUtils = GitHubUtils(cache_root, client_id, access_token)

        if revision is None:
            # Retrieve revision of latest codecov build
            github_revision = uploader.get_latest_codecov()
            self.revision = self.githubUtils.get_mercurial(github_revision)
            self.from_pulse = False
            suites_to_ignore = []
        else:
            self.revision = revision
            self.from_pulse = True
            suites_to_ignore = ['awsy', 'talos']
            self.notifier = Notifier(revision, client_id, access_token)

        logger.info('Mercurial revision', revision=self.revision)

        task_ids = {
            'linux': taskcluster.get_task('mozilla-central', self.revision, 'linux'),
            'windows': taskcluster.get_task('mozilla-central', self.revision, 'win'),
        }

        self.artifactsHandler = ArtifactsHandler(task_ids, suites_to_ignore)

    def generate_info(self, commit_sha=None, platform=None, suite=None, chunk=None, out_format='coveralls', options=[]):
        cmd = [
          'grcov',
          '-t', out_format,
          '-s', self.repo_dir,
          '-p', '/home/worker/workspace/build/src/',
          '--ignore-dir', 'gcc',
          '--ignore-not-existing',
        ]

        if 'coveralls' in out_format:
            r = requests.get('https://hg.mozilla.org/mozilla-central/json-rev/%s' % self.revision)
            r.raise_for_status()
            push_id = r.json()['pushid']

            cmd.extend([
              '--service-name', 'TaskCluster',
              '--service-number', str(push_id),
              '--commit-sha', commit_sha,
              '--token', secrets[secrets.COVERALLS_TOKEN] if self.from_pulse else 'NONE',
            ])

            if suite is not None:
                cmd.extend(['--service-job-number', str(self.suites.index(suite) + 1)])
            else:
                cmd.extend(['--service-job-number', '1'])

        cmd.extend(self.artifactsHandler.get(platform, suite, chunk))
        cmd.extend(options)

        return run_check(cmd)

    def generate_report(self, output, suite):
        info_file = '%s.info' % suite

        with open(info_file, 'wb') as f:
            f.write(output)

        run_check([
            'genhtml',
            '-o', os.path.join(os.getcwd(), suite),
            '--show-details', '--highlight', '--ignore-errors', 'source',
            '--legend', os.path.join(os.getcwd(), info_file),
            '--prefix', self.repo_dir
        ], cwd=self.repo_dir)

    def clone_mozilla_central(self, revision):
        shared_dir = self.repo_dir + '-shared'
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    'https://hg.mozilla.org/mozilla-central',
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)

        def do_clone():
            proc = hglib.util.popen(cmd)
            out, err = proc.communicate()
            if proc.returncode:
                raise hglib.error.CommandError(cmd, proc.returncode, out, err)

            hg = hglib.open(self.repo_dir)

            hg.update(rev=revision, clean=True)

        retry(do_clone)

        logger.info('mozilla-central cloned')

    def generate_per_suite_reports(self):
        def generate_suite_report(suite):
            output = self.generate_info(suite=suite, out_format='lcov')

            self.generate_report(output, suite)
            os.remove('%s.info' % suite)

            run_check(['tar', '-cjf', 'code-coverage-reports/%s.tar.bz2' % suite, suite])
            shutil.rmtree(os.path.join(os.getcwd(), suite))

            logger.info('Suite report generated', suite=suite)

        def generate_suite_report_task(suite):
            return lambda: generate_suite_report(suite)

        with ThreadPoolExecutor(max_workers=2) as executor:
            for suite in self.suites:
                executor.submit(generate_suite_report_task(suite))

    def generate_zero_coverage_report(self):
        report = self.generate_info(self.revision, out_format='coveralls+')
        report = json.loads(report.decode('utf-8'))  # Decoding is only necessary until Python 3.6.

        zero_coverage_files = []
        zero_coverage_functions = {}
        for sf in report['source_files']:
            name = sf['name']

            # For C/C++ source files, we can consider a file as being uncovered
            # when all its source lines are uncovered.
            all_lines_uncovered = all(c is None or c == 0 for c in sf['coverage'])
            # For JavaScript files, we can't do the same, as the top-level is always
            # executed, even if it just contains declarations. So, we need to check if
            # all its functions, except the top-level, are uncovered.
            all_functions_uncovered = True
            for f in sf['functions']:
                f_name = f['name']
                if f_name == 'top-level':
                    continue

                if not f['exec']:
                    if name in zero_coverage_functions:
                        zero_coverage_functions[name].append(f['name'])
                    else:
                        zero_coverage_functions[name] = [f['name']]
                else:
                    all_functions_uncovered = False

            if all_lines_uncovered or (len(sf['functions']) > 1 and all_functions_uncovered):
                zero_coverage_files.append(name)

        with open('code-coverage-reports/zero_coverage_files.json', 'w') as f:
            json.dump(zero_coverage_files, f)

        mkdir('code-coverage-reports/zero_coverage_functions')

        zero_coverage_function_counts = []
        for fname, functions in zero_coverage_functions.items():
            zero_coverage_function_counts.append({
                'name': fname,
                'funcs': len(functions),
            })
            with open('code-coverage-reports/zero_coverage_functions/%s.json' % fname.replace('/', '_'), 'w') as f:
                json.dump(functions, f)

        with open('code-coverage-reports/zero_coverage_functions.json', 'w') as f:
            json.dump(zero_coverage_function_counts, f)

    def generate_files_list(self, covered=True, platform=None, chunk=None):
        options = ['--filter-covered', '--threads', '2']
        files = self.generate_info(platform=platform, chunk=chunk, out_format='files', options=options)
        return files.splitlines()

    def generate_chunk_mapping(self):
        def get_files_task(platform, chunk):
            return lambda: (platform, chunk, self.generate_files_list(True, platform=platform, chunk=chunk))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for platform in ['linux', 'windows']:
                for chunk in self.artifactsHandler.get_chunks():
                    futures.append(executor.submit(get_files_task(platform, chunk)))

            with sqlite3.connect('chunk_mapping.sqlite') as conn:
                c = conn.cursor()
                c.execute('CREATE TABLE file_to_chunk (path text, platform text, chunk text)')
                c.execute('CREATE TABLE chunk_to_test (platform text, chunk text, path text)')

                for future in concurrent.futures.as_completed(futures):
                    (platform, chunk, files) = future.result()
                    c.executemany('INSERT INTO file_to_chunk VALUES (?,?,?)', ((f, platform, chunk) for f in files))

                try:
                    # Retrieve chunk -> tests mapping from ActiveData.
                    r = requests.post('https://activedata.allizom.org/query', data=json.dumps({
                        'from': 'unittest',
                        'where': {'and': [
                            {'eq': {'repo.branch.name': 'mozilla-central'}},
                            {'eq': {'repo.changeset.id12': self.revision[:12]}},
                            {'or': [
                                {'prefix': {'run.key': 'test-linux64-ccov'}},
                                {'prefix': {'run.key': 'test-windows10-64-ccov'}}
                            ]}
                        ]},
                        'limit': 50000,
                        'select': ['result.test', 'run.key']
                    }))

                    tests_data = r.json()['data']

                    task_names = tests_data['run.key']
                    test_iter = enumerate(tests_data['result.test'])
                    chunk_test_iter = ((taskcluster.get_platform(task_names[i]), taskcluster.get_chunk(task_names[i]), test) for i, test in test_iter)
                    c.executemany('INSERT INTO chunk_to_test VALUES (?,?,?)', chunk_test_iter)
                except:
                    # ActiveData is failing too often, so we need to ignore the error here.
                    pass

        tar = tarfile.open('code-coverage-reports/chunk_mapping.tar.xz', 'w:xz')
        tar.add('chunk_mapping.sqlite')
        tar.close()

    def go(self):
        with ThreadPoolExecutorResult(max_workers=2) as executor:
            # Thread 1 - Download coverage artifacts.
            executor.submit(lambda: self.artifactsHandler.download_all())

            # Thread 2 - Clone mozilla-central.
            executor.submit(lambda: self.clone_mozilla_central(self.revision))

        if self.from_pulse:
            self.githubUtils.update_geckodev_repo()

            commit_sha = self.githubUtils.get_commit(self.revision)
            logger.info('GitHub revision', revision=commit_sha)

            self.githubUtils.post_github_status(commit_sha)

            output = self.generate_info(commit_sha)
            logger.info('Report generated successfully')

            with ThreadPoolExecutorResult(max_workers=2) as executor:
                executor.submit(lambda: uploader.coveralls(output))
                executor.submit(lambda: uploader.codecov(output, commit_sha))

            logger.info('Waiting for build to be ingested by Codecov...')
            # Wait until the build has been ingested by Codecov.
            if uploader.codecov_wait(commit_sha):
                logger.info('Build ingested by codecov.io')
                self.notifier.notify()
            else:
                logger.info('codecov.io took too much time to ingest data.')
        else:
            mkdir('code-coverage-reports')

            self.generate_per_suite_reports()

            self.generate_zero_coverage_report()

            self.generate_chunk_mapping()

            os.chdir('code-coverage-reports')
            self.githubUtils.update_codecoveragereports_repo()
