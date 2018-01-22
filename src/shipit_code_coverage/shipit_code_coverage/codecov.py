# -*- coding: utf-8 -*-
import json
import os
import shutil
import tarfile
from zipfile import ZipFile
import requests
import hglib
from threading import Condition, Lock
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import time

from cli_common.log import get_logger
from cli_common.command import run_check
from cli_common.taskcluster import get_service

from shipit_code_coverage import taskcluster, uploader
from shipit_code_coverage.utils import mkdir, wait_until, retry, ThreadPoolExecutorResult


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

        self.gecko_dev_user = gecko_dev_user
        self.gecko_dev_pwd = gecko_dev_pwd
        self.client_id = client_id
        self.access_token = access_token

        if revision is None:
            self.task_ids = [
                taskcluster.get_last_task('linux'),
                taskcluster.get_last_task('win'),
            ]

            task_data = taskcluster.get_task_details(self.task_ids[0])
            self.revision = task_data['payload']['env']['GECKO_HEAD_REV']
            self.coveralls_token = 'NONE'
            self.codecov_token = 'NONE'
            self.from_pulse = False
        else:
            self.task_ids = [
                taskcluster.get_task('mozilla-central', revision, 'linux'),
                taskcluster.get_task('mozilla-central', revision, 'win'),
            ]
            self.revision = revision
            self.coveralls_token = coveralls_token
            self.codecov_token = codecov_token
            self.from_pulse = True

        self.build_finished = False
        self.build_finished_cv = Condition()

        if self.from_pulse:
            self.suites_to_ignore = ['awsy', 'talos']
        else:
            self.suites_to_ignore = []

        logger.info('Mercurial revision', revision=self.revision)

    def get_chunks(self):
        return list(set([f.split('_')[1] for f in os.listdir('ccov-artifacts')]))

    def get_coverage_artifacts(self, suite=None, chunk=None):
        files = os.listdir('ccov-artifacts')

        if suite is not None and chunk is not None:
            raise Exception('suite and chunk can\'t both have a value')

        filtered_files = []
        for fname in files:
            # grcov artifacts always have 'grcov' in the name and are ZIP files.
            if 'grcov' in fname and not fname.endswith('.zip'):
                continue
            # jsvm artifacts always have 'jsvm' in the name and are not ZIP files.
            if 'jsvm' in fname and fname.endswith('.zip'):
                continue

            # If suite and chunk are None, return all artifacts.
            # Otherwise, only return the ones which have suite or chunk in their name.
            if (
                   (suite is None and chunk is None) or
                   (suite is not None and ('%s' % suite) in fname) or
                   (chunk is not None and ('%s_code-coverage' % chunk) in fname)
               ):
                filtered_files.append('ccov-artifacts/' + fname)

        return filtered_files

    def download_coverage_artifacts(self):
        mkdir('ccov-artifacts')

        # The test tasks for the Linux and Windows builds are in the same group,
        # but the following code is generic and supports build tasks split in
        # separate groups.
        groups = set([taskcluster.get_task_details(build_task_id)['taskGroupId'] for build_task_id in self.task_ids])
        test_tasks = [
            task
            for group in groups
            for task in taskcluster.get_tasks_in_group(group)
            if taskcluster.is_coverage_task(task)
        ]

        FINISHED_STATUSES = ['completed', 'failed', 'exception']
        ALL_STATUSES = FINISHED_STATUSES + ['unscheduled', 'pending', 'running']

        downloaded_tasks = {}
        downloaded_tasks_lock = Lock()

        def should_download(status, chunk_name, platform_name):
            with downloaded_tasks_lock:
                if (chunk_name, platform_name) not in downloaded_tasks:
                    return True

                other_status = downloaded_tasks[(chunk_name, platform_name)]

                if (status == 'failed' and other_status == 'exception') or (status == 'completed' and other_status != 'completed'):
                    downloaded_tasks[(chunk_name, platform_name)] = status
                    return True
                else:
                    return False

        def download_artifact(test_task):
            status = test_task['status']['state']
            assert status in ALL_STATUSES
            while status not in FINISHED_STATUSES:
                time.sleep(60)
                status = taskcluster.get_task_status(test_task['status']['taskId'])['status']['state']
                assert status in ALL_STATUSES

            chunk_name = taskcluster.get_chunk_name(test_task)
            platform_name = taskcluster.get_platform_name(test_task)
            # Ignore awsy and talos as they aren't actually suites of tests.
            if any(to_ignore in chunk_name for to_ignore in self.suites_to_ignore):
                return

            # If we have already downloaded this chunk from another task, check if the
            # other task has a better status than this one.
            if not should_download(status, chunk_name, platform_name):
                return

            test_task_id = test_task['status']['taskId']
            for artifact in taskcluster.get_task_artifacts(test_task_id):
                if not any(n in artifact['name'] for n in ['code-coverage-grcov.zip', 'code-coverage-jsvm.zip']):
                    continue

                artifact_path = taskcluster.download_artifact(test_task_id, chunk_name, platform_name, artifact)
                logger.info('%s artifact downloaded' % artifact_path)
                if 'code-coverage-jsvm.zip' in artifact['name']:
                    self.rewrite_jsvm_lcov(artifact_path)
                    logger.info('%s artifact rewritten' % artifact_path)

        def download_artifact_task(test_task):
            return lambda: download_artifact(test_task)

        with ThreadPoolExecutorResult() as executor:
            for test_task in test_tasks:
                executor.submit(download_artifact_task(test_task))

        logger.info('Code coverage artifacts downloaded')

    def update_github_repo(self):
        run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
        repo_url = 'https://%s:%s@github.com/marco-c/gecko-dev' % (self.gecko_dev_user, self.gecko_dev_pwd)
        repo_path = os.path.join(self.cache_root, 'gecko-dev')

        if not os.path.isdir(repo_path):
            retry(lambda: run_check(['git', 'clone', repo_url], cwd=self.cache_root))
        retry(lambda: run_check(['git', 'pull', 'https://github.com/mozilla/gecko-dev', 'master'], cwd=repo_path))
        retry(lambda: run_check(['git', 'push', repo_url, 'master'], cwd=repo_path))

    def post_github_status(self, commit_sha):
        tcGithub = get_service('github', self.client_id, self.access_token)
        tcGithub.createStatus('marco-c', 'gecko-dev', commit_sha, {
            'state': 'success',
        })

    def get_github_commit(self, mercurial_commit):
        url = 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s'

        def get_commit():
            r = requests.get(url % mercurial_commit)

            if r.status_code == requests.codes.ok:
                return r.text.split(' ')[0]

            return None

        ret = wait_until(get_commit)
        if ret is None:
            raise Exception('Mercurial commit is not available yet on mozilla/gecko-dev.')
        return ret

    def rewrite_jsvm_lcov(self, zip_file_path):
        with self.build_finished_cv:
            while not self.build_finished:
                self.build_finished_cv.wait()

        out_dir = zip_file_path[:-4]
        out_file = out_dir + '.info'

        with ZipFile(zip_file_path, 'r') as z:
            z.extractall(out_dir)

        run_check([
            'gecko-env', './mach', 'python',
            'python/mozbuild/mozbuild/codecoverage/lcov_rewriter.py',
            os.path.abspath(out_dir),
            '--output-file', os.path.abspath(out_file)
        ], cwd=self.repo_dir)

        shutil.rmtree(out_dir)

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

        cmd.extend(self.get_coverage_artifacts(suite, chunk))
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

    def build_files(self):
        with open(os.path.join(self.repo_dir, '.mozconfig'), 'w') as f:
            f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-firefox\n')
            f.write('ac_add_options --enable-debug\n')
            f.write('ac_add_options --enable-artifact-builds\n')

        retry(lambda: run_check(['gecko-env', './mach', 'build'], cwd=self.repo_dir))
        retry(lambda: run_check(['gecko-env', './mach', 'build-backend', '-b', 'ChromeMap'], cwd=self.repo_dir))

        logger.info('Build successful')

        self.build_finished = True
        with self.build_finished_cv:
            self.build_finished_cv.notify_all()

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
            for chunk in self.get_chunks():
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
            executor.submit(lambda: self.download_coverage_artifacts())

            # Thread 2 - Clone and build mozilla-central
            clone_future = executor.submit(lambda: self.clone_mozilla_central(self.revision))
            # Make sure cloning mozilla-central didn't fail before building.
            clone_future.add_done_callback(lambda f: f.result())
            # Now we can build.
            clone_future.add_done_callback(lambda f: self.build_files())

        if self.from_pulse:
            if self.gecko_dev_user is not None and self.gecko_dev_pwd is not None:
                self.update_github_repo()

            commit_sha = self.get_github_commit(self.revision)
            logger.info('GitHub revision', revision=commit_sha)

            if self.gecko_dev_user is not None and self.gecko_dev_pwd is not None:
                self.post_github_status(commit_sha)

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
            run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
            run_check(['git', 'config', '--global', 'user.email', 'report@upload.it'])
            run_check(['git', 'config', '--global', 'user.name', 'Report Uploader'])
            repo_url = 'https://%s:%s@github.com/marco-c/code-coverage-reports' % (self.gecko_dev_user, self.gecko_dev_pwd)
            run_check(['git', 'init'])
            run_check(['git', 'add', '*'])
            run_check(['git', 'commit', '-m', 'Coverage reports upload'])
            retry(lambda: run_check(['git', 'push', repo_url, 'master', '--force']))
