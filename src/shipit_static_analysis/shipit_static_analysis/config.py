# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from cli_common.log import get_logger
import yaml
import requests


PROJECT_NAME = 'shipit-static-analysis'
CONFIG_URL = 'https://hg.mozilla.org/mozilla-central/raw-file/tip/tools/clang-tidy/config.yaml'

logger = get_logger(__name__)


class Settings(object):
    def __init__(self):
        self.config = None
        self.download({
            'cpp_extensions': ['.cpp', '.c', '.h'],
        })
        assert 'clang_checkers' in self.config
        assert 'target' in self.config

    def __getattr__(self, key):
        if key not in self.config:
            raise AttributeError
        return self.config[key]

    def download(self, defaults={}):
        '''
        Configuration is stored on mozilla central
        It has to be downloaded on each run
        '''
        assert isinstance(defaults, dict)
        assert self.config is None, \
            'Config already set.'
        resp = requests.get(CONFIG_URL)
        assert resp.ok, \
            'Failed to retrieve configuration from mozilla-central #{}'.format(resp.status_code)  # noqa

        self.config = defaults
        self.config.update(yaml.load(resp.content))
        logger.info('Loaded configuration from mozilla-central')

    def is_publishable_check(self, check):
        '''
        Is this check publishable ?
        Support the wildcard expansion
        '''
        for c in self.clang_checkers:
            name = c['name']

            if name.endswith('*') and check.startswith(name[:-1]):
                # Wildcard at end of check name
                return c['publish']

            elif name == check:
                # Same exact check name
                return c['publish']

        return False


# Shared instance
settings = Settings()
