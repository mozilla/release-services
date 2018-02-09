# -*- coding: utf-8 -*-
import json
import os
import shutil
import tarfile
import requests
import hglib
from threading import Lock
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


class Notifier(object):

    def __init__(self, revision, emails, client_id, access_token):
        self.revision = revision
        self.emails = emails
        self.notify_service = get_service('notify', client_id, access_token)

    def prepopulate_cache(self, commit_sha):
        content = ''

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

                r = requests.get('https://uplift.shipit.staging.mozilla-releng.net/coverage/changeset/%s' % changeset['node'])
        except Exception as e:
            logger.warn('Error while requesting coverage data', error=str(e))

        if content == '':
            return;
        elif len(content) > 102400:
            # Content is 102400 chars max
            content = content[:102000] + '\n\n... Content max limit reached!'

        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': 'Coverage patches for %s' % self.revision,
                'content': content,
                'template': 'fullscreen',
            })
