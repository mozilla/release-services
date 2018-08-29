# -*- coding: utf-8 -*-
import os
import shutil
import tarfile
from datetime import datetime
from datetime import timedelta

import hglib
import requests

from cli_common.command import run_check
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from cli_common.utils import ThreadPoolExecutorResult
from shipit_code_coverage import chunk_mapping
from shipit_code_coverage import grcov
from shipit_code_coverage import taskcluster
from shipit_code_coverage import uploader
from shipit_code_coverage.artifacts import ArtifactsHandler
from shipit_code_coverage.github import GitHubUtils
from shipit_code_coverage.notifier import Notifier
from shipit_code_coverage.secrets import secrets
from shipit_code_coverage.zero_coverage import ZeroCov

logger = get_logger(__name__)


class CodeCov(object):

    def __init__(self, revision, cache_root, client_id, access_token):
        # List of test-suite, sorted alphabetically.
        # This way, the index of a suite in the array should be stable enough.
        self.suites = [
            'web-platform-tests',
        ]

        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        self.client_id = client_id
        self.access_token = access_token

        self.index_service = get_service('index', client_id, access_token)

        self.githubUtils = GitHubUtils(cache_root, client_id, access_token)

        if revision is None:
            # Retrieve revision of latest codecov build
            self.github_revision = uploader.get_latest_codecov()
            self.revision = self.githubUtils.git_to_mercurial(self.github_revision)
            self.from_pulse = False
            suites_to_ignore = []
        else:
            self.github_revision = None
            self.revision = revision
            self.from_pulse = True
            suites_to_ignore = ['awsy', 'talos']
            self.notifier = Notifier(self.repo_dir, revision, client_id, access_token)

        logger.info('Mercurial revision', revision=self.revision)

        task_ids = {
            'linux': taskcluster.get_task('mozilla-central', self.revision, 'linux'),
            'windows': taskcluster.get_task('mozilla-central', self.revision, 'win'),
            'android-test': taskcluster.get_task('mozilla-central', self.revision, 'android-test'),
            'android-emulator': taskcluster.get_task('mozilla-central', self.revision, 'android-emulator'),
        }

        self.artifactsHandler = ArtifactsHandler(task_ids, suites_to_ignore)

    def clone_mozilla_central(self, revision):
        shared_dir = self.repo_dir + '-shared'
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    'https://hg.mozilla.org/mozilla-central',
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    revision=revision,
                                    networkattempts=7)

        cmd.insert(0, hglib.HGPATH)

        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        logger.info('mozilla-central cloned')

    def generate_suite_reports(self):
        for suite in self.suites:
            output = grcov.report(self.artifactsHandler.get(suite=suite), out_format='lcov')

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

            os.remove('%s.info' % suite)

            with tarfile.open('code-coverage-reports/%s.tar.xz' % suite, 'w:xz') as tar:
                tar.add(suite)
            shutil.rmtree(os.path.join(os.getcwd(), suite))

            logger.info('Suite report generated', suite=suite)

    def go(self):
        if self.from_pulse:
            commit_sha = self.githubUtils.mercurial_to_git(self.revision)
            try:
                uploader.get_codecov(commit_sha)
                logger.warn('Build was already injested')
                return
            except requests.exceptions.HTTPError:
                pass

        with ThreadPoolExecutorResult(max_workers=2) as executor:
            # Thread 1 - Download coverage artifacts.
            executor.submit(self.artifactsHandler.download_all)

            # Thread 2 - Clone mozilla-central.
            executor.submit(self.clone_mozilla_central, self.revision)

        if self.from_pulse:
            self.githubUtils.update_geckodev_repo()

            logger.info('GitHub revision', revision=commit_sha)

            self.githubUtils.post_github_status(commit_sha)

            r = requests.get('https://hg.mozilla.org/mozilla-central/json-rev/%s' % self.revision)
            r.raise_for_status()
            push_id = r.json()['pushid']

            output = grcov.report(
                self.artifactsHandler.get(),
                source_dir=self.repo_dir,
                service_number=push_id,
                commit_sha=commit_sha,
                token=secrets[secrets.COVERALLS_TOKEN]
            )
            logger.info('Report generated successfully')

            with ThreadPoolExecutorResult(max_workers=2) as executor:
                executor.submit(uploader.coveralls, output)
                executor.submit(uploader.codecov, output, commit_sha)

            logger.info('Waiting for build to be ingested by Codecov...')
            # Wait until the build has been ingested by Codecov.
            if uploader.codecov_wait(commit_sha):
                logger.info('Build ingested by codecov.io')
                self.notifier.notify()
            else:
                logger.error('codecov.io took too much time to ingest data.')
        else:
            logger.info('Generating suite reports')
            os.makedirs('code-coverage-reports', exist_ok=True)
            self.generate_suite_reports()

            logger.info('Generating zero coverage reports')
            zc = ZeroCov(self.repo_dir)
            zc.generate(self.artifactsHandler.get(), self.revision, self.github_revision)

            logger.info('Generating chunk mapping')
            chunk_mapping.generate(self.repo_dir, self.revision, self.artifactsHandler)

            # Index the task in the TaskCluster index at the given revision and as "latest".
            # Given that all tasks have the same rank, the latest task that finishes will
            # overwrite the "latest" entry.
            namespaces = [
                'project.releng.services.project.{}.shipit_code_coverage.{}'.format(secrets[secrets.APP_CHANNEL], self.revision),
                'project.releng.services.project.{}.shipit_code_coverage.latest'.format(secrets[secrets.APP_CHANNEL]),
            ]

            for namespace in namespaces:
                self.index_service.insertTask(
                    namespace,
                    {
                        'taskId': os.environ['TASK_ID'],
                        'rank': 0,
                        'data': {},
                        'expires': (datetime.utcnow() + timedelta(180)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    }
                )

            os.chdir('code-coverage-reports')
            self.githubUtils.update_codecoveragereports_repo()
