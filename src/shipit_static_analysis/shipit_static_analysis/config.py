# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import os
import yaml


PROJECT_NAME = 'shipit-static-analysis'


class Settings(object):
    def __init__(self):
        # Read local config from yaml
        config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
        self.config = yaml.load(open(config_path))
        assert 'clang_checkers' in self.config
        assert 'target' in self.config

    def __getattr__(self, key):
        if key not in self.config:
            raise AttributeError
        return self.config[key]

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
