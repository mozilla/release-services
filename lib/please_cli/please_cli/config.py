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
        'update': True,
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
            'data_dir': os.path.join(TMP_DIR, 'redis'),
        },
    },
    'notification/policy': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8006,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-notif-policy',
                        'heroku_dyno_type': 'web',
                        'url': 'https://policy.notification.testing.mozilla-releng.net',
                        'dns': 'policy.notification.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-notif-policy',
                        'heroku_dyno_type': 'web',
                        'url': 'https://policy.notification.staging.mozilla-releng.net',
                        'dns': 'policy.notification.staging.mozilla-releng.net.herokudns.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-notif-policy',
                        'heroku_dyno_type': 'web',
                        'url': 'https://policy.notification.mozilla-releng.net',
                        'dns': 'policy.notification.mozilla-releng.net.herokudns.com',
                    },
                },
            },
        ],
    },
    'notification/identity': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8007,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-notif-identity',
                        'heroku_dyno_type': 'web',
                        'url': 'https://identity.notification.testing.mozilla-releng.net',
                        'dns': 'identity.notification.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-notif-identity',
                        'heroku_dyno_type': 'web',
                        'url': 'https://identity.notification.staging.mozilla-releng.net',
                        'dns': 'identity.notification.staging.mozilla-releng.net.herokudns.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-notif-ident',
                        'heroku_dyno_type': 'web',
                        'url': 'https://identity.notification.mozilla-releng.net',
                        'dns': 'identity.notification.mozilla-releng.net.herokudns.com',
                    },
                },
            },
        ],
    },
    'docs': {
        'update': True,
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
                        's3_bucket': 'releng-testing-docs',
                        'url': 'https://docs.testing.mozilla-releng.net',
                        'dns': 'd1sw5c8kdn03y.cloudfront.net.',
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'releng-staging-docs',
                        'url': 'https://docs.staging.mozilla-releng.net',
                        'dns': 'd32jt14rospqzr.cloudfront.net.',
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'releng-production-docs',
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
            'tokens/api',
            'treestatus/api',
            'mapper/api',
            'notification/policy',
            'notification/identity',
        ],
        'deploys': [
            {
                'target': 'S3',
                'options': {
                    'testing': {
                        'enable': True,
                        's3_bucket': 'releng-testing-frontend',
                        'url': 'https://testing.mozilla-releng.net',
                        'dns': 'd1l70lpksx3ik7.cloudfront.net.',
                        'csp': [
                            'https://login.taskcluster.net',
                            'https://auth.taskcluster.net',
                        ],
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'releng-staging-frontend',
                        'url': 'https://staging.mozilla-releng.net',
                        'dns': 'dpwmwa9tge2p3.cloudfront.net.',
                        'csp': [
                            'https://login.taskcluster.net',
                            'https://auth.taskcluster.net',
                        ],
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'releng-production-frontend',
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
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8004,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-mapper',
                        'heroku_dyno_type': 'web',
                        'url': 'https://mapper.testing.mozilla-releng.net',
                        'dns': 'mapper.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-mapper',
                        'heroku_dyno_type': 'web',
                        'url': 'https://mapper.staging.mozilla-releng.net',
                        'dns': 'mapper.staging.mozilla-releng.net.herokudns.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-mapper',
                        'heroku_dyno_type': 'web',
                        'url': 'https://mapper.mozilla-releng.net',
                        'dns': 'mapper.mozilla-releng.net.herokudns.com',
                    },
                },
            },
        ],
    },
    'tokens/api': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8003,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-tokens',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tokens.testing.mozilla-releng.net',
                        'dns': 'tokens.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-tokens',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tokens.staging.mozilla-releng.net',
                        'dns': 'tokens.staging.mozilla-releng.net.herokudns.com',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-tokens',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tokens.mozilla-releng.net',
                        'dns': 'tokens.mozilla-releng.net.herokudns.com',
                    },
                },
            },
        ],
    },
    'tooltool/api': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8002,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-tooltool',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tooltool.testing.mozilla-releng.net',
                        'dns': 'shizuoka-60622.herokussl.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-tooltool',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tooltool.staging.mozilla-releng.net',
                        'dns': 'shizuoka-60622.herokussl.com',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-tooltool',
                        'heroku_dyno_type': 'web',
                        'url': 'https://tooltool.mozilla-releng.net',
                        'dns': 'kochi-11433.herokussl.com',
                    },
                },
            },
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-tooltool',
                        'heroku_dyno_type': 'worker',
                        'heroku_command': '/bin/flask worker',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-tooltool',
                        'heroku_dyno_type': 'worker',
                        'heroku_command': '/bin/flask worker',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-tooltool',
                        'heroku_dyno_type': 'worker',
                        'heroku_command': '/bin/flask worker',
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
                        'enable': False,
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
                        'enable': False,
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
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8000,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-testing-treestatus',
                        'heroku_dyno_type': 'web',
                        'url': 'https://treestatus.testing.mozilla-releng.net',
                        # TODO: we need to change this to SSL Endpoint
                        'dns': 'treestatus.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-staging-treestatus',
                        'heroku_dyno_type': 'web',
                        'url': 'https://treestatus.staging.mozilla-releng.net',
                        # TODO: we need to change this to SSL Endpoint
                        'dns': 'nagasaki-25852.herokussl.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'releng-production-treestatus',
                        'heroku_dyno_type': 'web',
                        'url': 'https://treestatus.mozilla-releng.net',
                        # TODO: this needs to be updated in mozilla-releng/build-cloud-tools
                        'dns': 'kochi-31413.herokussl.com',
                    },
                },
            },
        ],
    },
    'uplift/bot': {
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'codecoverage/bot': {
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'codecoverage/backend': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8011,
        },
        'requires': [
            'redis',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-testing-codecoverage',
                        'heroku_dyno_type': 'web',
                        'url': 'https://coverage.testing.moz.tools',
                        'dns': 'coverage.testing.moz.tools.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-staging-codecoverage',
                        'heroku_dyno_type': 'web',
                        'url': 'https://coverage.staging.moz.tools',
                        'dns': 'coverage.staging.moz.tools.herokudns.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-production-codecoverage',
                        'heroku_dyno_type': 'web',
                        'url': 'https://coverage.moz.tools',
                        'dns': 'coverage.moz.tools.herokudns.com',
                    },
                },
            },
        ],
    },
    'codecoverage/crawler': {
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'bugbug/data': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'bugbug/train': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'bugbug/eval': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': False,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ],
    },
    'pulselistener': {
        'requires': [],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-testing-pulse-listener',
                        'heroku_dyno_type': 'worker',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-staging-pulse-listener',
                        'heroku_dyno_type': 'worker',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-production-pulse-listen',
                        'heroku_dyno_type': 'worker',
                    },
                },
            },
        ],
    },
    'staticanalysis/bot': {
        'deploys': [
            {
                'target': 'TASKCLUSTER_HOOK',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.testing',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.staging',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'deploy.production',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                    },
                },
            },
        ]
    },
    'staticanalysis/frontend': {
        'update': False,
        'run': 'NEUTRINO',
        'run_options': {
            'port': 8010,
            'envs': {
                'CONFIG': 'dev',
            },
        },
        'requires': [],
        'deploys': [
            {
                'target': 'S3',
                'options': {

                    'testing': {
                        'enable': True,
                        's3_bucket': 'release-services-staticanalysis-frontend-testing',
                        'url': 'https://static-analysis.testing.moz.tools',
                        'dns': 'd1blqs705aw8h9.cloudfront.net.',
                        'envs': {
                            # Use the same API as staging
                            'CONFIG': 'staging',
                        },
                        'csp': [
                            'https://index.taskcluster.net',
                            'https://queue.taskcluster.net',
                            'https://taskcluster-artifacts.net',
                        ],
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'release-services-staticanalysis-frontend-staging',
                        'url': 'https://static-analysis.staging.moz.tools',
                        'dns': 'd21hzgxp28m0tc.cloudfront.net.',
                        'envs': {
                            'CONFIG': 'staging',
                        },
                        'csp': [
                            'https://index.taskcluster.net',
                            'https://queue.taskcluster.net',
                            'https://taskcluster-artifacts.net',
                        ],
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'release-services-staticanalysis-frontend-production',
                        'url': 'https://static-analysis.moz.tools',
                        'dns': 'd2ezri92497z3m.cloudfront.net.',
                        'envs': {
                            'CONFIG': 'production',
                        },
                        'csp': [
                            'https://index.taskcluster.net',
                            'https://queue.taskcluster.net',
                            'https://taskcluster-artifacts.net',
                        ],
                    },
                },
            },
        ],
    },
    'uplift/backend': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8011,
        },
        'requires': [
            'postgresql',
        ],
        'deploys': [
            {
                'target': 'HEROKU',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-testing-uplift',
                        'heroku_dyno_type': 'web',
                        'url': 'https://uplift.shipit.testing.mozilla-releng.net',
                        'dns': 'uplift.shipit.testing.mozilla-releng.net.herokudns.com',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-staging-uplift',
                        'heroku_dyno_type': 'web',
                        'url': 'https://uplift.shipit.staging.mozilla-releng.net',
                        'dns': 'uplift.shipit.staging.mozilla-releng.net.herokudns.com',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'docker',
                        'heroku_app': 'shipit-production-uplift',
                        'heroku_dyno_type': 'web',
                        'url': 'https://uplift.shipit.mozilla-releng.net',
                        'dns': 'uplift.shipit.mozilla-releng.net.herokudns.com',
                    },
                },
            },
        ],
    },
    'shipit/api': {
        'update': True,
        'run': 'FLASK',
        'run_options': {
            'port': 8015,
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
                        'url': 'https://api.shipit.testing.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                    'staging': {
                        'enable': True,
                        'url': 'https://api.shipit.staging.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                    'production': {
                        'enable': True,
                        # TODO: we will switch to new url soon
                        # 'url': 'https://api.shipit.mozilla-releng.net',
                        'url': 'https://shipit-api.mozilla-releng.net',
                        'nix_path_attribute': 'dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                },
            },
            {
                'target': 'DOCKERHUB',
                'options': {
                    'testing': {
                        'enable': True,
                        'nix_path_attribute': 'worker_dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                    'staging': {
                        'enable': True,
                        'nix_path_attribute': 'worker_dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                    'production': {
                        'enable': True,
                        'nix_path_attribute': 'worker_dockerflow',
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozilla/shipitbackend',
                    },
                },
            },
        ],
    },
    'shipit/frontend': {
        'update': False,
        'run': 'NEUTRINO',
        'run_options': {
            'port': 8010,
            'envs': {
                'CONFIG': 'dev',
            },
        },
        'requires': [
            'shipit/api',
        ],
        'deploys': [
            {
                'target': 'S3',
                'options': {
                    'testing': {
                        'enable': True,
                        's3_bucket': 'shipit-testing-frontend',
                        'url': 'https://shipit.testing.mozilla-releng.net',
                        'dns': 'd2jpisuzgldax2.cloudfront.net.',
                        'envs': {
                            # Use the same API as staging
                            'CONFIG': 'testing',
                        },
                        'csp': [
                            'https://hg.mozilla.org',
                            'https://queue.taskcluster.net',
                            'https://auth.mozilla.auth0.com',
                        ],
                    },
                    'staging': {
                        'enable': True,
                        's3_bucket': 'shipit-staging-frontend',
                        'url': 'https://shipit.staging.mozilla-releng.net',
                        'dns': 'd2ld4e8bl8yd1l.cloudfront.net.',
                        'envs': {
                            'CONFIG': 'staging',
                        },
                        'csp': [
                            'https://hg.mozilla.org',
                            'https://queue.taskcluster.net',
                            'https://auth.mozilla.auth0.com',
                        ],
                    },
                    'production': {
                        'enable': True,
                        's3_bucket': 'shipit-production-frontend',
                        'url': 'https://shipit.mozilla-releng.net',
                        'dns': 'dve8yd1431ifz.cloudfront.net.',
                        'envs': {
                            'CONFIG': 'production',
                        },
                        'csp': [
                            'https://hg.mozilla.org',
                            'https://queue.taskcluster.net',
                            'https://auth.mozilla.auth0.com',
                        ],
                    },
                },
            },
        ],
    },
}
