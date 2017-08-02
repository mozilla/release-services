# -*- coding: utf-8 -*-
import errno
import os
from datetime import datetime
import zipfile
import requests
import hglib
from threading import Condition

from cli_common.log import get_logger
from cli_common.command import run_check

from shipit_code_coverage import taskcluster, uploader
from shipit_code_coverage.utils import wait_until, retry, ThreadPoolExecutorResult


logger = get_logger(__name__)


class CodeCov(object):

    def __init__(self, revision, cache_root, coveralls_token, codecov_token, gecko_dev_user, gecko_dev_pwd):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = []

        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        self.coveralls_token = coveralls_token
        self.codecov_token = codecov_token
        self.gecko_dev_user = gecko_dev_user
        self.gecko_dev_pwd = gecko_dev_pwd

        if revision is None:
            self.task_id = taskcluster.get_last_task()

            task_data = taskcluster.get_task_details(self.task_id)
            self.revision = task_data['payload']['env']['GECKO_HEAD_REV']
        else:
            self.task_id = taskcluster.get_task('mozilla-central', revision)
            self.revision = revision

        self.build_finished = False
        self.build_finished_cv = Condition()

        logger.info('Mercurial revision', revision=self.revision)

    def download_coverage_artifacts(self, build_task_id):
        try:
            os.mkdir('ccov-artifacts')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        task_data = taskcluster.get_task_details(build_task_id)

        all_suites = set()

        def rewriting_task(path):
            return lambda: self.rewrite_jsvm_lcov(path)

        tasks = taskcluster.get_tasks_in_group(task_data['taskGroupId'])
        test_tasks = [t for t in tasks if taskcluster.is_coverage_task(t)]
        with ThreadPoolExecutorResult() as executor:
            for test_task in test_tasks:
                suite_name = taskcluster.get_suite_name(test_task)
                # Ignore awsy and talos as they aren't actually suites of tests.
                if any(to_ignore in suite_name for to_ignore in ['awsy', 'talos']):
                    continue

                all_suites.add(suite_name)

                test_task_id = test_task['status']['taskId']
                for artifact in taskcluster.get_task_artifacts(test_task_id):
                    if not any(n in artifact['name'] for n in ['code-coverage-grcov.zip', 'code-coverage-jsvm.zip']):
                        continue

                    artifact_path = taskcluster.download_artifact(test_task_id, suite_name, artifact)
                    if 'code-coverage-jsvm.zip' in artifact['name']:
                        executor.submit(rewriting_task(artifact_path))

            self.suites = list(all_suites)
            self.suites.sort()

            logger.info('Code coverage artifacts downloaded')

    def update_github_repo(self):
        run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
        repo_url = 'https://%s:%s@github.com/marco-c/gecko-dev' % (self.gecko_dev_user, self.gecko_dev_pwd)
        repo_path = os.path.join(self.cache_root, 'gecko-dev')

        if not os.path.isdir(repo_path):
            retry(lambda: run_check(['git', 'clone', repo_url], cwd=self.cache_root))
        retry(lambda: run_check(['git', 'pull', 'https://github.com/mozilla/gecko-dev', 'master'], cwd=repo_path))
        retry(lambda: run_check(['git', 'push', repo_url, 'master'], cwd=repo_path))

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

        zip_file = zipfile.ZipFile(zip_file_path, 'r')
        zip_file.extractall(out_dir)
        zip_file.close()

        lcov_files = [os.path.abspath(os.path.join(out_dir, f)) for f in os.listdir(out_dir)]
        run_check(['gecko-env', './mach', 'python', 'python/mozbuild/mozbuild/codecoverage/lcov_rewriter.py'] + lcov_files, cwd=self.repo_dir)

        for lcov_file in lcov_files:
            os.remove(lcov_file)

        lcov_out_files = [os.path.abspath(os.path.join(out_dir, f)) for f in os.listdir(out_dir)]
        for lcov_out_file in lcov_out_files:
            os.rename(lcov_out_file, lcov_out_file[:-4])

    def generate_info(self, commit_sha, coveralls_token, suite=None):
        files = os.listdir('ccov-artifacts')
        ordered_files = []
        for fname in files:
            if 'grcov' in fname and not fname.endswith('.zip'):
                continue
            if 'jsvm' in fname and fname.endswith('.zip'):
                continue

            if suite is None or suite in fname:
                ordered_files.append('ccov-artifacts/' + fname)

        cmd = [
          'grcov',
          '-t', 'coveralls',
          '-s', self.repo_dir,
          '-p', '/home/worker/workspace/build/src/',
          '--ignore-dir', 'gcc',
          '--ignore-not-existing',
          '--service-name', 'TaskCluster',
          '--service-number', datetime.today().strftime('%Y%m%d'),
          '--commit-sha', commit_sha,
          '--token', coveralls_token,
        ]

        if suite is not None:
            cmd.extend(['--service-job-number', str(self.suites.index(suite) + 1)])
        else:
            cmd.extend(['--service-job-number', '1'])

        cmd.extend(ordered_files)

        return run_check(cmd, cwd=os.getcwd())

    def clone_mozilla_central(self, revision):
        shared_dir = self.repo_dir + '-shared'
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    'https://hg.mozilla.org/mozilla-central',
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)
        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        hg = hglib.open(self.repo_dir)

        hg.update(rev=revision, clean=True)

        logger.info('mozilla-central cloned')

    def build_files(self):
        with open(os.path.join(self.repo_dir, '.mozconfig'), 'w') as f:
            f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-firefox\n')
            f.write('ac_add_options --enable-debug\n')
            f.write('ac_add_options --enable-artifact-builds\n')

        run_check(['gecko-env', './mach', 'build'], cwd=self.repo_dir)
        run_check(['gecko-env', './mach', 'build-backend', '-b', 'ChromeMap'], cwd=self.repo_dir)

        logger.info('Build successful')

        self.build_finished = True
        with self.build_finished_cv:
            self.build_finished_cv.notify_all()

    def go(self):
        with ThreadPoolExecutorResult(max_workers=2) as executor:
            # Thread 1 - Download coverage artifacts.
            executor.submit(lambda: self.download_coverage_artifacts(self.task_id))

            # Thread 2 - Clone and build mozilla-central
            clone_future = executor.submit(lambda: self.clone_mozilla_central(self.revision))
            clone_future.add_done_callback(lambda f: self.build_files())

        if self.gecko_dev_user is not None and self.gecko_dev_pwd is not None:
            self.update_github_repo()

        commit_sha = self.get_github_commit(self.revision)
        logger.info('GitHub revision', revision=commit_sha)

        # TODO: Process suites in parallel.
        # While we are uploading results for a suite, we can start to process the next one.
        # TODO: Reenable when Coveralls and/or Codecov will be able to properly handle the load.
        '''for suite in self.suites:
            output = self.generate_info(commit_sha, self.coveralls_token, suite)

            logger.info('Suite report generated', suite=suite)

            uploader.coveralls(output)
            uploader.codecov(output, commit_sha, self.codecov_token, [suite.replace('-', '_')])'''

        output = self.generate_info(commit_sha, self.coveralls_token)
        logger.info('Report generated successfully')

        with ThreadPoolExecutorResult(max_workers=2) as executor:
            executor.submit(lambda: uploader.coveralls(output))
            executor.submit(lambda: uploader.codecov(output, commit_sha, self.codecov_token))
