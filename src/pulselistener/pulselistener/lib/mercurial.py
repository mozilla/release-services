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
import time

import hglib
import structlog
from libmozdata.phabricator import PhabricatorPatch

from pulselistener.lib.phabricator import PhabricatorBuild
from pulselistener.lib.utils import batch_checkout
from pulselistener.lib.utils import robust_checkout

logger = structlog.get_logger(__name__)

TREEHERDER_URL = 'https://treeherder.mozilla.org/#/jobs?repo={}&revision={}'


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
        self.checkout_mode = config.get('checkout', 'batch')
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
        # Start by updating the repo using batch checkout
        logger.info('Checking out tip', repo=self.url, mode=self.checkout_mode)
        if self.checkout_mode == 'batch':
            batch_checkout(self.url, self.dir, b'tip', self.batch_size)
        elif self.checkout_mode == 'robust':
            robust_checkout(self.url, self.dir, b'tip')
        else:
            raise Exception('Unsupported clone mode', mode=self.checkout_mode)
        logger.info('Full checkout finished')

        # Setup repo in main process
        self.repo = hglib.open(self.dir)
        self.repo.setcbout(lambda msg: logger.info('Mercurial', stdout=msg))
        self.repo.setcberr(lambda msg: logger.info('Mercurial', stderr=msg))

    def has_revision(self, revision):
        '''
        Check if a revision is available on this Mercurial repo
        '''
        if not revision:
            return False
        try:
            self.repo.identify(revision)
            return True
        except hglib.error.CommandError:
            return False

    def apply_build(self, build):
        '''
        Apply a stack of patches to mercurial repo
        and commit them one by one
        '''
        assert isinstance(build, PhabricatorBuild)
        assert len(build.stack) > 0, 'No patches to apply'
        assert all(map(lambda p: isinstance(p, PhabricatorPatch), build.stack))

        # Find the first unknown base revision
        needed_stack = []
        for patch in reversed(build.stack):
            needed_stack.insert(0, patch)

            # Stop as soon as a base revision is available
            if self.has_revision(patch.base_revision):
                logger.info('Stopping at revision {}'.format(patch.base_revision))
                break

        if not needed_stack:
            logger.info('All the patches are already applied')
            return

        # When base revision is missing, update to default revision
        hg_base = needed_stack[0].base_revision
        if not self.has_revision(hg_base):
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

        for patch in needed_stack:
            message = ''
            if patch.commits:
                message += '{}\n'.format(patch.commits[0]['message'])
            message += 'Differential Diff: {}'.format(patch.phid)

            logger.info('Applying patch', phid=patch.phid, message=message)
            self.repo.import_(
                patches=io.BytesIO(patch.patch.encode('utf-8')),
                message=message,
                user='pulselistener',
            )

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
            diff_phid = build.stack[-1].phid
            message = 'try_task_config for code-review\nDifferential Diff: {}'.format(diff_phid)

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


class MercurialWorker(object):
    '''
    Mercurial worker maintaining several local clones
    '''
    def __init__(self, queue_name, queue_phabricator, repositories):
        assert all(map(lambda r: isinstance(r, Repository), repositories.values()))
        self.queue_name = queue_name
        self.queue_phabricator = queue_phabricator
        self.repositories = repositories

    def register(self, bus):
        self.bus = bus
        self.bus.add_queue(self.queue_name)

    async def run(self):
        # First clone all repositories
        for repo in self.repositories.values():
            logger.info('Cloning repo {}'.format(repo))
            repo.clone()

        # Wait for phabricator diffs to apply
        while True:
            build = await self.bus.receive(self.queue_name)
            assert isinstance(build, PhabricatorBuild)

            # Find the repository from the diff and trigger the build on it
            repository = self.repositories.get(build.repo_phid)
            if repository is not None:
                result = self.handle_build(repository, build)
                await self.bus.send(self.queue_phabricator, result)

            else:
                logger.error('Unsupported repository', repo=build.repo_phid, build=build)

    def handle_build(self, repository, build):
        '''
        Try to load and apply a diff on local clone
        If successful, push to try and send a treeherder link
        If failure, send a unit result with a warning message
        '''
        assert isinstance(repository, Repository)
        start = time.time()

        try:
            # Start by cleaning the repo
            repository.clean()

            # First apply patches on local repo
            repository.apply_build(build)

            # Configure the try task
            repository.add_try_commit(build)

            # Then push that stack on try
            tip = repository.push_to_try()
            logger.info('Diff has been pushed !')

            # Publish Treeherder link
            uri = TREEHERDER_URL.format(repository.try_name, tip.node.decode('utf-8'))
        except hglib.error.CommandError as e:
            # Format nicely the error log
            error_log = e.err
            if isinstance(error_log, bytes):
                error_log = error_log.decode('utf-8')

            logger.warn('Mercurial error on diff', error=error_log, args=e.args, build=build)
            return ('fail:mercurial', build, {'message': error_log, 'duration': time.time() - start})

        except Exception as e:
            logger.warn('Failed to process diff', error=e, build=build)
            return ('fail:general', build, {'message': str(e), 'duration': time.time() - start})

        return ('success', build, {'treeherder_url': uri})
