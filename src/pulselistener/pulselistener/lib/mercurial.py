# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
import enum
import io
import json
import os
import tempfile

import hglib
from libmozdata.phabricator import revision_available

from cli_common.log import get_logger
from cli_common.mercurial import batch_checkout
from pulselistener.lib.phabricator import PhabricatorPatch

logger = get_logger(__name__)


class TryMode(enum.Enum):
    json = 'json'
    syntax = 'syntax'


class Repository(object):
    '''
    A Mercurial repository with its try server credentials
    '''
    def __init__(self, config, cache_root):
        assert isinstance(config, dict)
        self.name = config['name']
        self.url = config['url']
        self.dir = os.path.join(cache_root, config['name'])
        self.batch_size = config.get('batch_size', 10000)
        self.try_url = config['try_url']
        self.try_mode = TryMode(config.get('try_mode', 'json'))
        self.try_syntax = config.get('try_syntax')
        self.try_name = config.get('try_name', 'try')
        self.default_revision = config.get('default_revision', 'tip')
        if self.try_mode == TryMode.syntax:
            assert self.try_syntax, 'Missing try syntax'

        # Write ssh key from secret
        _, self.ssh_key_path = tempfile.mkstemp(suffix='.key')
        with open(self.ssh_key_path, 'w') as f:
            f.write(config['ssh_key'])

        # Build ssh conf
        conf = {
            'StrictHostKeyChecking': 'no',
            'User': config['ssh_user'],
            'IdentityFile': self.ssh_key_path,
        }
        self.ssh_conf = 'ssh {}'.format(' '.join('-o {}="{}"'.format(k, v) for k, v in conf.items())).encode('utf-8')

        # Remove key when finished
        self.repo = None
        atexit.register(self.end_of_life)

    def __str__(self):
        return self.name

    def end_of_life(self):
        os.unlink(self.ssh_key_path)
        logger.info('Removed ssh key')

    def clone(self):
        # Clone using batch checkout
        logger.info('Cloning repo', repo=self.name)
        batch_checkout(self.url, self.dir, b'tip', self.batch_size)
        logger.info('Batch checkout finished')

        # Setup repo in main process
        self.repo = hglib.open(self.dir)
        self.repo.setcbout(lambda msg: logger.info('Mercurial', stdout=msg))
        self.repo.setcberr(lambda msg: logger.info('Mercurial', stderr=msg))

    async def apply_patches(self, stack):
        '''
        Apply a stack of patches to mercurial repo
        and commit them one by one
        '''
        assert isinstance(stack, list)
        assert len(stack) > 0, 'No patches to apply'
        assert all(map(lambda p: isinstance(p, PhabricatorPatch), stack)), 'Only patches are supported'

        # When base revision is missing, update to default revision
        hg_base = stack[0].base_revision
        if hg_base is None or not revision_available(self.repo, hg_base):
            logger.warning('Missing base revision {} from Phabricator'.format(hg_base))
            hg_base = self.default_revision

        # Update the repo to base revision
        try:
            logger.info('Updating repo to revision {}'.format(hg_base))
            self.repo.update(
                rev=hg_base,
                clean=True,
            )
        except hglib.error.CommandError:
            raise Exception('Failed to update to revision {}'.format(hg_base))

        # Get current revision using full informations tuple from hglib
        revision = self.repo.identify(id=True).strip()
        revision = self.repo.log(revision, limit=1)[0]
        logger.info('Updated repo', revision=revision.node, repo=self.name)

        for diff in stack:
            message = ''
            if diff.commits:
                message += '{}\n'.format(diff.commits[0]['message'])
            message += 'Differential Diff: {}'.format(diff.phid)

            logger.info('Applying patch', phid=diff.phid, message=message)
            self.repo.import_(
                patches=io.BytesIO(diff.patch.encode('utf-8')),
                message=message,
                user='pulselistener',
            )

            # Use parent until a base revision is available in the repository
            # This is needed to support stack of patches with already merged patches
            if diff.base_revision and revision_available(self.repo, diff.base_revision):
                logger.info('Found available revision', revision=diff.base_revision, repo=self.name)
                break

    def add_try_commit(self, build):
        '''
        Build and commit the file configuring try
        * always try_task_config.json
        * MC payload in json mode
        * custom simpler payload on syntax mode
        '''
        path = os.path.join(self.dir, 'try_task_config.json')
        if self.try_mode == TryMode.json:
            config = {
                'version': 2,
                'parameters': {
                    'target_tasks_method': 'codereview',
                    'optimize_target_tasks': True,
                    'phabricator_diff': build.target_phid,
                }
            }
            message = 'try_task_config for code-review\nDifferential Diff: {}'.format(build.diff['phid'])

        elif self.try_mode == TryMode.syntax:
            config = {
                'version': 2,
                'parameters': {
                    'code-review': {
                        'phabricator-build-target': build.target_phid,
                    }
                }
            }
            message = 'try: {}'.format(self.try_syntax)

        else:
            raise Exception('Unsupported try mode')

        # Write content as json and commit it
        with open(path, 'w') as f:
            json.dump(config, f, sort_keys=True, indent=4)
        self.repo.add(path.encode('utf-8'))
        self.repo.commit(
            message=message,
            user='pulselistener',
        )

    def push_to_try(self):
        '''
        Push the current tip on remote try repository
        '''
        tip = self.repo.tip()
        logger.info('Pushing patches to try', rev=tip.node)
        self.repo.push(
            dest=self.try_url.encode('utf-8'),
            rev=tip.node,
            ssh=self.ssh_conf,
            force=True,
        )
        return tip

    def clean(self):
        '''
        Steps to clean the mercurial repo
        '''
        logger.info('Remove uncommited changes')
        self.repo.revert(self.dir.encode('utf-8'), all=True)

        logger.info('Remove all mercurial drafts')
        try:
            cmd = hglib.util.cmdbuilder(b'strip', rev=b'roots(outgoing())', force=True, backup=False)
            self.repo.rawcommand(cmd)
        except hglib.error.CommandError as e:
            if b'abort: empty revision set' not in e.err:
                raise

        logger.info('Pull updates from remote repo')
        self.repo.pull()
