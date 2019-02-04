# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import atexit
import io
import os
import tempfile

from cli_common.log import get_logger
from cli_common.mercurial import robust_checkout
from pulselistener.config import REPO_TRY

logger = get_logger(__name__)


class MercurialWorker(object):
    '''
    Mercurial worker maintaining a local clone of Mozilla-Central
    '''
    def __init__(self, phabricator_api, ssh_user, ssh_key, repo_url, repo_dir):
        self.repo_url = repo_url
        self.repo_dir = repo_dir
        self.phabricator_api = phabricator_api

        # Build asyncio shared queue
        self.queue = asyncio.Queue()

        # Write ssh key from secret
        _, self.ssh_key_path = tempfile.mkstemp(suffix='.key')
        with open(self.ssh_key_path, 'w') as f:
            f.write(ssh_key)

        # Build ssh conf
        conf = {
            'StrictHostKeyChecking': 'no',
            'User': ssh_user,
            'IdentityFile': self.ssh_key_path,
        }
        self.ssh_conf = 'ssh {}'.format(' '.join('-o {}="{}"'.format(k, v) for k, v in conf.items())).encode('utf-8')

        # Remove key when finished
        atexit.register(self.cleanup)

    def cleanup(self):
        os.unlink(self.ssh_key_path)
        logger.info('Removed ssh key')

    async def run(self):

        # Update to tip
        logger.info('Checking out tip of {}'.format(self.repo_url))
        self.repo = robust_checkout(self.repo_url, self.repo_dir)
        logger.info('Initial clone finished')

        # Wait for phabricator diffs to apply
        while True:
            diff = await self.queue.get()
            assert isinstance(diff, dict)
            assert 'phid' in diff

            try:
                await self.handle_diff(diff)
            except Exception as e:
                logger.info('Failed to process diff', error=e, phid=diff['phid'])

                # Remove uncommited changes
                self.repo.revert(self.repo_dir.encode('utf-8'), all=True)

            # Notify the queue that the message has been processed
            self.queue.task_done()

    async def handle_diff(self, diff):
        '''
        Handle a new diff received from Phabricator:
        - apply revision to mercurial repo
        - trigger push-to-try
        '''
        logger.info('Received diff {phid}'.format(**diff))

        # Get the stack of patches
        patches = self.phabricator_api.load_patches_stack(self.repo, diff)

        # Apply the patches, without commiting
        for diff_phid, patch in patches:
            logger.info('Applying patch', phid=diff_phid)
            self.repo.import_(
                patches=io.BytesIO(patch.encode('utf-8')),
                nocommit=True,
            )

        # Make a single commit with all these patches
        _, commit = self.repo.commit(
            message='Code review for {phid}'.format(**diff),
            addremove=True,
            user='pulselistener',
        )

        # Push the commit on try
        logger.info('Pushing patches to try', rev=commit)
        self.repo.push(
            dest=REPO_TRY,
            rev=commit,
            ssh=self.ssh_conf,
        )
