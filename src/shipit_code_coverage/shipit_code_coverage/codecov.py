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

from shipit_code_coverage import taskcluster, uploader
from shipit_code_coverage.artifacts import ArtifactsHandler
from shipit_code_coverage.github import GitHubUtils
from shipit_code_coverage.utils import mkdir, retry, ThreadPoolExecutorResult


logger = get_logger(__name__)


class CodeCov(object):

    def __init__(self, revision, cache_root, coveralls_token, codecov_token,
                 gecko_dev_user, gecko_dev_pwd, client_id, access_token):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = [
            'cppunit', 'gtest', 'web-platform-tests', 'talos',
        ]

        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        if revision is None:
            task_ids = {
                'linux': taskcluster.get_last_task('linux'),
                'windows': taskcluster.get_last_task('win'),
            }

            task_data = taskcluster.get_task_details(task_ids['linux'])
            self.revision = task_data['payload']['env']['GECKO_HEAD_REV']
            self.coveralls_token = 'NONE'
            self.codecov_token = 'NONE'
            # Ignore awsy and talos as they aren't actually suites of tests.
            suites_to_ignore = ['awsy', 'talos']
            self.from_pulse = False
        else:
            task_ids = {
                'linux': taskcluster.get_task('mozilla-central', revision, 'linux'),
                'windows': taskcluster.get_task('mozilla-central', revision, 'win'),
            }
            self.revision = revision
            self.coveralls_token = coveralls_token
            self.codecov_token = codecov_token
            suites_to_ignore = []
            self.from_pulse = True

        logger.info('Mercurial revision', revision=self.revision)

        self.artifactsHandler = ArtifactsHandler(task_ids, suites_to_ignore)
        self.githubUtils = GitHubUtils(cache_root, gecko_dev_user, gecko_dev_pwd, client_id, access_token)

    def generate_info(self, commit_sha=None, suite=None, chunk=None, out_format='coveralls', options=[]):
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
              '--token', self.coveralls_token,
            ])

            if suite is not None:
                cmd.extend(['--service-job-number', str(self.suites.index(suite) + 1)])
            else:
                cmd.extend(['--service-job-number', '1'])

        cmd.extend(self.artifactsHandler.get_coverage_artifacts(suite, chunk))
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

        retry(lambda: do_clone())

        logger.info('mozilla-central cloned')

    def prepopulate_cache(self, commit_sha):
        try:
            logger.info('Waiting for build to be ingested by Codecov...')
            # Wait until the build has been ingested by Codecov.
            if uploader.codecov_wait(commit_sha):
                logger.info('Build ingested by codecov.io')
            else:
                logger.info('codecov.io took too much time to ingest data.')
                return

            # Get pushlog and ask the backend to generate the coverage by changeset
            # data, which will be cached.
            r = requests.get('https://hg.mozilla.org/mozilla-central/json-pushes?changeset=%s&version=2&full' % self.revision)
            r.raise_for_status()
            data = r.json()
            changesets = data['pushes'][data['lastpushid']]['changesets']

            for changeset in changesets:
                if any(text in changeset['desc'] for text in ['r=merge', 'a=merge']):
                    continue

                requests.get('https://uplift.shipit.staging.mozilla-releng.net/coverage/changeset/%s' % changeset['node'])
        except Exception as e:
            logger.warn('Error while requesting coverage data', error=str(e))

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

    def generate_files_list(self, covered=True, chunk=None):
        options = ['--filter-covered', '--threads', '2']
        files = self.generate_info(chunk=chunk, out_format='files', options=options)
        return files.splitlines()

    def generate_chunk_mapping(self):
        def get_files_task(chunk):
            return lambda: (chunk, self.generate_files_list(True, chunk=chunk))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for chunk in self.artifactsHandler.get_chunks():
                futures.append(executor.submit(get_files_task(chunk)))

            with sqlite3.connect('chunk_mapping.db') as conn:
                c = conn.cursor()
                c.execute('CREATE TABLE files (path text, chunk text)')

                for future in concurrent.futures.as_completed(futures):
                    (chunk, files) = future.result()
                    c.executemany('INSERT INTO files VALUES (?,?)', [(f, chunk) for f in files])

        tar = tarfile.open('code-coverage-reports/chunk_mapping.tar.xz', 'w:xz')
        tar.add('chunk_mapping.db')
        tar.close()

    def go(self):
        with ThreadPoolExecutorResult(max_workers=2) as executor:
            # Thread 1 - Download coverage artifacts.
            executor.submit(lambda: self.artifactsHandler.download_coverage_artifacts())

            # Thread 2 - Clone mozilla-central.
            executor.submit(lambda: self.clone_mozilla_central(self.revision))

        if self.from_pulse:
            self.githubUtils.update_geckodev_repo()

            commit_sha = self.githubUtils.get_commit(self.revision)
            logger.info('GitHub revision', revision=commit_sha)

            self.githubUtils.post_status(commit_sha)

            output = self.generate_info(commit_sha)
            logger.info('Report generated successfully')

            with ThreadPoolExecutorResult(max_workers=2) as executor:
                executor.submit(lambda: uploader.coveralls(output))
                executor.submit(lambda: uploader.codecov(output, commit_sha, self.codecov_token))

            self.prepopulate_cache(commit_sha)
        else:
            mkdir('code-coverage-reports')

            self.generate_per_suite_reports()

            self.generate_zero_coverage_report()

            self.generate_chunk_mapping()

            os.chdir('code-coverage-reports')
            self.githubUtils.update_codecoveragereports_repo()
