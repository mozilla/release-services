# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import os

import click

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

DOCKER_BASE_REGISTRY = 'index.docker.io'
DOCKER_BASE_REPO = 'mozillareleng/services'
DOCKER_BASE_TAG = 'base-' + VERSION

NIX_BIN_DIR = os.environ.get('NIX_BIN_DIR', '')  # must end with /
OPENSSL_BIN_DIR = os.environ.get('OPENSSL_BIN_DIR', '')  # must end with /
OPENSSL_ETC_DIR = os.environ.get('OPENSSL_ETC_DIR', '')  # must end with /
POSTGRESQL_BIN_DIR = os.environ.get('POSTGRESQL_BIN_DIR', '')  # must end with /

IN_DOCKER = False
if os.path.exists('/proc/1/cgroup'):
    with open('/proc/1/cgroup', 'rt') as ifh:
        IN_DOCKER = 'docker' in ifh.read()

TEMPLATES = {
    'backend-json-api': {}
}

DEV_PROJECTS = ['postgresql', 'redis']
PROJECTS = list(map(lambda x: x.replace('_', '-')[len(SRC_DIR) + 1:],
                    filter(lambda x: os.path.exists(os.path.join(SRC_DIR, x, 'default.nix')),
                           glob.glob(SRC_DIR + '/*') + glob.glob(SRC_DIR + '/*/*'))))
PROJECTS += DEV_PROJECTS


# TODO: below data should be placed in src/<app>/default.nix files alongside
PROJECTS_CONFIG = {
    'common/naming': {
        'update': False,
    },
    'postgresql': {
        'update': False,
        'run': 'POSTGRESQL',
        'run_options': {
            'port': 9000,
            'data_dir': os.path.join(TMP_DIR, 'postgresql'),
        },
    },
    'redis': {
        'update': False,
        'run': 'REDIS',
        'run_options': {
            'port': 6379,
            'schema': 'redis',
            'data_dir': os.path.join(TMP_DIR, 'redis'),
        },
    },
    'docs': {
        'update': False,
        'run': 'SPHINX',
        'run_options': {
            'schema': 'http',
            'port': 7000,
        },
        'deploys': [
            {
                'target': 'S3',
                'options': {
                    'testing': {
                        'enable': True,
                        's3_bucket': 'relengstatic-testing-relengdocs-static-website',
                        'url': 'https://docs.testing.mozilla-releng.net',
                        'dns': 'd1sw5c8kdn03y.cloudfront.net.',
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'relengstatic-staging-relengdocs-static-website',
                        'url': 'https://docs.staging.mozilla-releng.net',
                        'dns': 'd32jt14rospqzr.cloudfront.net.',
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'relengstatic-prod-relengdocs-static-website',
                        'url': 'https://docs.mozilla-releng.net',
                        'dns': 'd1945er7u4liht.cloudfront.net.',
                    },
                },
            },
        ],
    },
    'releng-frontend': {
        'update': False,
        'run': 'ELM',
        'run_options': {
            'port': 8010,
        },
        'requires': [
            'docs',
            'tooltool/api',
            'treestatus/api',
        ],
        'deploys': [
            {
                'target': 'S3',
                'options': {
                    'testing': {
                        'enable': True,
                        's3_bucket': 'relengstatic-testing-relengfrontend-static-website',
                        'url': 'https://testing.mozilla-releng.net',
                        'dns': 'd1l70lpksx3ik7.cloudfront.net.',
                        'csp': [
                            'https://login.taskcluster.net',
                            'https://auth.taskcluster.net',
                        ],
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'relengstatic-staging-relengfrontend-static-website',
                        'url': 'https://staging.mozilla-releng.net',
                        'dns': 'dpwmwa9tge2p3.cloudfront.net.',
                        'csp': [
                            'https://login.taskcluster.net',
                            'https://auth.taskcluster.net',
                        ],
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'relengstatic-prod-relengfrontend-static-website',
                        'url': 'https://mozilla-releng.net',
                        'dns': 'd1qqwps52z1e12.cloudfront.net.',
                        'dns_domain': 'www.mozilla-releng.net',
                        'csp': [
                            'https://login.taskcluster.net',
                            'https://auth.taskcluster.net',
                        ],
                    },
                },
            },
        ],
    },
    'mapper/api': {
        'update': False,
        'run': 'FLASK',
        'run_options': {
            'port': 8004,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'DOCKERHUB',
                'options': {
                    'testing': {
                        'enable': True,
                        'url': 'https://dev.mapper.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'mapper_api_dockerflow_testing',
                    },
                    'staging': {
                        'enable': True,
                        'url': 'https://stage.mapper.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'mapper_api_dockerflow_staging',
                    },
                    'production': {
                        'enable': True,
                        'url': 'https://mapper.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'mapper_api_dockerflow_production',
                    },
                },
            },
        ],
    },
    'tooltool/client': {
        'update': False,
    },
    'tooltool/api': {
        'update': False,
        'run': 'FLASK',
        'run_options': {
            'port': 8002,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'DOCKERHUB',
                'options': {
                    'testing': {
                        'enable': True,
                        'url': 'https://dev.tooltool.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'tooltool_api_dockerflow_testing',
                    },
                    'staging': {
                        'enable': True,
                        'url': 'https://stage.tooltool.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'tooltool_api_dockerflow_staging',
                    },
                    'production': {
                        'enable': True,
                        'url': 'https://tooltool.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'tooltool_api_dockerflow_production',
                    },
                },
            },
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'cron.replicate.testing',
                        'name-suffix': '-replicate',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'cron.replicate.staging',
                        'name-suffix': '-replicate',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'cron.replicate.production',
                        'name-suffix': '-replicate',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'cron.check_pending_uploads.testing',
                        'name-suffix': '-check_pending_uploads',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'cron.check_pending_uploads.staging',
                        'name-suffix': '-check_pending_uploads',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'cron.check_pending_uploads.production',
                        'name-suffix': '-check_pending_uploads',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'treestatus/api': {
        'update': False,
        'run': 'FLASK',
        'run_options': {
            'port': 8000,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'DOCKERHUB',
                'options': {
                    'testing': {
                        'enable': True,
                        'url': 'https://dev.treestatus.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'treestatus_api_dockerflow_testing',
                    },
                    'staging': {
                        'enable': True,
                        'url': 'https://stage.treestatus.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'treestatus_api_dockerflow_staging',
                    },
                    'production': {
                        'enable': True,
                        'url': 'https://treestatus.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'treestatus_api_dockerflow_production',
                    },
                },
            },
        ],
    },
    'scriptworker/shipitscript': {
        'update': False,
        'deploys': [
            {
                'target': 'DOCKERHUB',
                'options': {
                    'testing': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'scriptworker_shipitscript_docker_testing',
                    },
                    'staging': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'scriptworker_shipitscript_docker_staging',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/release-services',
                        'docker_stable_tag': 'scriptworker_shipitscript_docker_production',
                    },
                },
            },
        ],
    },
}
