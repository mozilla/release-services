# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

import click
import yaml

CWD_DIR = os.path.abspath(os.getcwd())

NO_ROOT_DIR_ERROR = '''Project root directory couldn't be detected.

`please` file couln't be found in any of the following folders:
%s
'''

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    VERSION = f.read().strip()

ROOT_DIR = None
_folders = []
for item in reversed(CWD_DIR.split(os.sep)):
    item_dir = '/' + CWD_DIR[:CWD_DIR.find(item) + len(item)][1:]
    _folders.append(item_dir)
    if os.path.isfile(os.path.join(item_dir, 'please')):
        ROOT_DIR = item_dir
        break

if ROOT_DIR is None:
    raise click.ClickException(NO_ROOT_DIR_ERROR % '\n - '.join(_folders))

CACHE_URLS = [
    'https://cache.mozilla-releng.net',
]

SRC_DIR = os.path.join(ROOT_DIR, 'src')
TMP_DIR = os.path.join(ROOT_DIR, 'tmp')

CHANNELS = ['master', 'testing', 'staging', 'production']
DEPLOY_CHANNELS = ['testing', 'staging', 'production']

DOCKER_REGISTRY = "https://index.docker.io"
DOCKER_REPO = 'mozillareleng/services'
DOCKER_BASE_TAG = 'base-' + VERSION

NIX_BIN_DIR = os.environ.get("NIX_BIN_DIR", "")  # must end with /
OPENSSL_BIN_DIR = os.environ.get("OPENSSL_BIN_DIR", "")  # must end with /
OPENSSL_ETC_DIR = os.environ.get("OPENSSL_ETC_DIR", "")  # must end with /
POSTGRESQL_BIN_DIR = os.environ.get("POSTGRESQL_BIN_DIR", "")  # must end with /

IN_DOCKER = False
with open('/proc/1/cgroup', 'rt') as ifh:
    IN_DOCKER = 'docker' in ifh.read()

TEMPLATES = {
    'backend-json-api': {}
}

# Load projects and their configuration from src dir.
PROJECTS = list(map(lambda x: x.replace('_', '-'),
                    filter(lambda x: os.path.exists(os.path.join(SRC_DIR, x, 'default.nix')),
                           os.listdir(SRC_DIR))))

PROJECTS_CONFIG = {
    project: yaml.load(open(os.path.join(SRC_DIR, project.replace('-', '_'), 'config.yml')))
    for project in PROJECTS
}

# Add postgresql
PROJECTS += ['postgresql']
PROJECTS_CONFIG.update({
    'postgresql': {
        'run': 'POSTGRESQL',
        'run_options': {
            'port': 9000,
            'data_dir': os.path.join(TMP_DIR, 'postgresql'),
        },
    },
})
