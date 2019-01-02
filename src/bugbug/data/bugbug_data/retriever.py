# -*- coding: utf-8 -*-

import lzma
import os
import shutil
from datetime import datetime
from datetime import timedelta

import hglib
from bugbug import bugzilla
from bugbug import labels
from bugbug import repository

from bugbug_data.secrets import secrets
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from cli_common.utils import ThreadPoolExecutorResult

logger = get_logger(__name__)


class Retriever(object):
    def __init__(self, cache_root, client_id, access_token):
        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)
        self.repo_dir = os.path.join(cache_root, 'mozilla-central')

        self.client_id = client_id
        self.access_token = access_token

        self.index_service = get_service('index', client_id, access_token)

    def retrieve_commits(self):
        shared_dir = self.repo_dir + '-shared'
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    'https://hg.mozilla.org/mozilla-central',
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    networkattempts=7,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)

        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        logger.info('mozilla-central cloned')

        repository.download_commits(self.repo_dir)

        logger.info('commit data extracted from repository')

        self.compress_file('data/commits.json')

    def retrieve_bugs(self):
        bugzilla.set_token(secrets[secrets.BUGZILLA_TOKEN])

        six_months_ago = datetime.utcnow() - timedelta(182)
        two_years_and_six_months_ago = six_months_ago - timedelta(365)
        logger.info('Downloading bugs from {} to {}'.format(two_years_and_six_months_ago, six_months_ago))
        bugzilla.download_bugs_between(two_years_and_six_months_ago, six_months_ago)

        logger.info('Downloading labelled bugs')
        bug_ids = labels.get_all_bug_ids()
        bugzilla.download_bugs(bug_ids)

        self.compress_file('data/bugs.json')

    def compress_file(self, path):
        with open(path, 'rb') as input_f:
            with lzma.open('{}.xz'.format(path), 'wb') as output_f:
                shutil.copyfileobj(input_f, output_f)

    def go(self):
        with ThreadPoolExecutorResult(max_workers=2) as executor:
            # Thread 1 - Download Bugzilla data.
            executor.submit(self.retrieve_bugs)

            # Thread 2 - Clone mozilla-central and retrieve commit data.
            executor.submit(self.retrieve_commits)

        # Index the task in the TaskCluster index.
        self.index_service.insertTask(
            'project.releng.services.project.{}.bugbug_data.latest'.format(secrets[secrets.APP_CHANNEL]),
            {
                'taskId': os.environ['TASK_ID'],
                'rank': 0,
                'data': {},
                'expires': (datetime.utcnow() + timedelta(31)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        )
