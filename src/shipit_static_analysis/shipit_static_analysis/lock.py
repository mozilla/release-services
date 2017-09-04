# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import uuid
from cli_common.log import get_logger

logger = get_logger(__name__)

LOCK_FILE = 'static-analysis.lock'


class LockDir(object):
    def __init__(self, root, prefix):
        assert os.path.isdir(root), \
            'Root {} is not a dir.'.format(root)

        self.root = root
        self.prefix = prefix
        self.lock = None

    def __enter__(self):
        '''
        Acquire a lock on the working directory for this task
        So that other tasks do not use it and remove artifacts
        Try to re-use an existing directory
        '''

        # List existing directories
        for directory in os.scandir(self.root):

            # Skip extras files/dirs
            if not directory.is_dir() or not directory.name.startswith(self.prefix):
                continue

            # Try to lock this directory
            if self.acquire_lock(directory.path):
                return directory.path

        # No directory found: create new one
        new_dir = os.path.join(
            self.root,
            self.prefix + uuid.uuid4().hex[:8]
        )
        if not self.acquire_lock(new_dir):
            raise Exception('Failed to lock new directory {}'.format(new_dir))
        return new_dir

    def __exit__(self, type, value, traceback):
        '''
        Unlock the directory
        '''
        assert self.lock is not None, \
            'Missing lock reference'
        assert os.path.exists(self.lock), \
            'Missing lock file {}'.format(self.lock)
        os.unlink(self.lock)
        logger.info('Unlocked', directory=self.lock)

    def acquire_lock(self, directory):
        # Check file is not locked
        self.lock = os.path.join(directory, LOCK_FILE)
        if os.path.exists(self.lock):
            logger.debug('Skipping already locked', directory=directory)
            return False

        if not os.path.isdir(directory):
            os.makedirs(directory)

        # Touch lock file
        with open(self.lock, 'a'):
            logger.info('Locking', directory=directory)
            os.utime(self.lock, None)
        return True
