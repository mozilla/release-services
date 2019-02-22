# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import toml

import cli_common.cli
import cli_common.log

log = cli_common.log.get_logger(__name__)


def deep_merge(base, override):
    '''
    Recursive deep merge of two dicts, applying ovveride onto base
    '''
    assert isinstance(base, dict)
    assert isinstance(override, dict)
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = deep_merge(base[k], v)
        else:
            base[k] = v
    return base


class ProjectConfig(object):
    '''
    Config per project, deep-merging several files by order:
    - user preferences: ~/.config/please/config.toml
    - root config: config.toml
    - project config: path/to/project/config.toml
    '''
    def __init__(self, project='please'):
        self.data = {}

        # User preferences folder
        xdg = os.path.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config'))
        home = os.path.join(xdg, 'please')
        if not os.path.isdir(home):
            os.makedirs(home)

        self.user_config_path = os.path.join(home, 'config.toml')
        paths = [
            self.user_config_path,
            os.path.join(os.getcwd(), 'config.toml'),
        ]

        # Deep merge new config onto current config
        for path in paths:
            self.data = deep_merge(self.data, self.load_file(path))

    def load_file(self, path):
        '''
        Load a TOML config from a local file
        '''
        if not os.path.exists(path):
            log.info('Missing local config', path=path)
            return {}

        data = toml.load(open(path))
        log.info('Read local config', path=path)

        return data

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            raise KeyError

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data.keys())

    def write_user_config(self, config):
        '''
        Update local user preferences
        '''
        user_config = deep_merge(self.load_file(self.user_config_path), config)
        with open(self.user_config_path, 'w') as f:
            toml.dump(user_config, f)
            log.info('Updated local config', path=self.user_config_path)
