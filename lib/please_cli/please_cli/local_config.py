# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import toml

import cli_common.cli
import cli_common.log

log = cli_common.log.get_logger(__name__)


class LocalConfig(object):
    '''
    Config for developers, in their home folder
    '''
    def __init__(self):
        self.path = os.path.expanduser('~/.pleaserc')
        if os.path.exists(self.path):
            self.data = toml.load(open(self.path))
            log.info('Read local config', path=self.path)
        else:
            self.data = {}
            log.info('No local config found')

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            raise KeyError

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data.keys())

    def write(self):
        with open(self.path, 'w') as f:
            toml.dump(self.data, f)
            log.info('Updated local config', path=self.path)
