# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import click

CWD_DIR = os.path.abspath(os.getcwd())

NO_ROOT_DIR_ERROR = '''Project root directory couldn't be detected.

`please` file couln't be found in any of the following folders:
%s
'''


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

CACHE_URL = "https://cache.mozilla-releng.net"

SRC_DIR = os.path.join(ROOT_DIR, 'src')
TMP_DIR = os.path.join(ROOT_DIR, 'tmp')

CHANNELS = ['master', 'staging', 'production']
DEPLOY_CHANNELS = ['staging', 'production']

DOCKER_REGISTRY = "https://index.docker.io"
DOCKER_REPO = 'mozillareleng/services'
DOCKER_BASE_TAG = 'base-latest'
DOCKER_BASE_SHA256 = '1835331e726eae803a7207989ed9c7db03e9fa98bab323df357fd27490576c39'

NIX_BIN_DIR = os.environ.get("NIX_BIN_DIR", "")  # must end with /
OPENSSL_BIN_DIR = os.environ.get("OPENSSL_BIN_DIR", "")  # must end with /
OPENSSL_ETC_DIR = os.environ.get("OPENSSL_ETC_DIR", "")  # must end with /
POSTGRESQL_BIN_DIR = os.environ.get("POSTGRESQL_BIN_DIR", "")  # must end with /

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as f:
    VERSION = f.read().strip()

IN_DOCKER = False
with open('/proc/1/cgroup', 'rt') as ifh:
    IN_DOCKER = 'docker' in ifh.read()


# TODO: below data should be placed in src/<app>/default.nix files alongside
PROJECTS = {
    'postgresql': {
        'run': 'POSTGRESQL',
        'run_options': {
            'port': 9000,
            'data_dir': os.path.join(TMP_DIR, 'postgresql'),
        },
    },
    'releng-notification-policy': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8006,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-notif-policy',
                'heroku_dyno_type': 'web',
                'url': 'https://policy.notification.staging.mozilla-releng.net',
                'dns': 'policy.notification.staging.mozilla-releng.net.herokudns.com',
            },
            'production': {
                'heroku_app': 'releng-production-notif-policy',
                'heroku_dyno_type': 'web',
                'url': 'https://policy.notification.mozilla-releng.net',
                'dns': 'policy.notification..mozilla-releng.net.herokudns.com',
            },
        },
    },
    'releng-notification-identity': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8007,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-notif-identity',
                'heroku_dyno_type': 'web',
                'url': 'https://identity.notification.staging.mozilla-releng.net',
                'dns': 'identity.notification.staging.mozilla-releng.net.herokudns.com',
            },
            'production': {
                'heroku_app': 'releng-production-notif-ident',
                'heroku_dyno_type': 'web',
                'url': 'https://identity.notification.mozilla-releng.net',
                'dns': 'identity.notification..mozilla-releng.net.herokudns.com',
            },
        },
    },
    'releng-archiver': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8005,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-archiver',
                'heroku_dyno_type': 'web',
                'url': 'https://archiver.staging.mozilla-releng.net',
                # TODO: switch to SSL Endpoint
                'dns': 'archiver.staging.mozilla-releng.net.herokudns.com',
            },
            # 'production': {
            #     'heroku_app': 'releng-production-archiver',
            #     'heroku_dyno_type': 'web',
            #     'url': 'https://archiver.mozilla-releng.net',
            #     # TODO: switch to SSL Endpoint
            #     'dns': 'archiver.mozilla-releng.net.herokudns.com',
            # },
        },
    },
    'releng-clobberer': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8001,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-clobberer',
                'heroku_dyno_type': 'web',
                'url': 'https://clobberer.staging.mozilla-releng.net',
                # TODO: do staging and production have the same dns?
                'dns': 'saitama-70467.herokussl.com',
            },
            # 'production': {
            #     'heroku_app': 'releng-production-clobberer',
            #     'heroku_dyno_type': 'web',
            #     'url': 'https://clobberer.mozilla-releng.net',
            #     'dns': 'saitama-70467.herokussl.com',
            # },
        },
    },
    'releng-docs': {
        'run': 'SPHINX',
        'run_options': {
            'schema': 'http',
            'port': 7000,
        },
        'deploy': 'S3',
        'deploy_options': {
            'staging': {
                's3_bucket': 'releng-staging-docs',
                'url': 'https://docs.staging.mozilla-releng.net',
                'dns': 'd32jt14rospqzr.cloudfront.net.',
            },
            'production': {
                's3_bucket': 'releng-production-docs',
                'url': 'https://docs.mozilla-releng.net',
                'dns': 'd1945er7u4liht.cloudfront.net.',
            },
        }
    },
    'releng-frontend': {
        'run': 'ELM',
        'run_options': {
            'port': 8000,
        },
        'requires': [
            'releng-docs',
            'releng-clobberer',
            'releng-tooltool',
            'releng-treestatus',
            'releng-mapper',
            'releng-archiver',
            'releng-notification-policy',
            'releng-notification-identity',
        ],
        'deploy': 'S3',
        'deploy_options': {
            'staging': {
                's3_bucket': 'releng-staging-frontend',
                'url': 'https://staging.mozilla-releng.net',
                'dns': 'dpwmwa9tge2p3.cloudfront.net.',
                'csp': [
                    'https://login.taskcluster.net',
                    'https://auth.taskcluster.net',
                ],
            },
            'production': {
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
    'releng-mapper': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8004,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-mapper',
                'heroku_dyno_type': 'web',
                'url': 'https://mapper.staging.mozilla-releng.net',
                # TODO: switch to SSL Endpoint
                'dns': 'mapper.staging.mozilla-releng.net.herokudns.com',
            },
            # 'production': {
            #     'heroku_app': 'releng-production-mapper',
            #     'heroku_dyno_type': 'web',
            #      # TODO: switch to SSL Endpoint
            #     'url': 'https://mapper.mozilla-releng.net',
            #     'dns': 'mapper.mozilla-releng.net.herokudns.com',
            # },
        },
    },
    'releng-tooltool': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8002,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-tooltool',
                'heroku_dyno_type': 'web',
                'url': 'https://tooltool.staging.mozilla-releng.net',
                'dns': 'shizuoka-60622.herokussl.com',
            },
            'production': {
                'heroku_app': 'releng-production-tooltool',
                'heroku_dyno_type': 'web',
                'url': 'https://tooltool.mozilla-releng.net',
                'dns': 'kochi-11433.herokussl.com',
            },
        },
    },
    'releng-treestatus': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8003,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'releng-staging-treestatus',
                'heroku_dyno_type': 'web',
                'url': 'https://treestatus.staging.mozilla-releng.net',
                # TODO: we need to change this to SSL Endpoint
                'dns': 'treestatus.staging.mozilla-releng.net.herokudns.com',
            },
            'production': {
                'heroku_app': 'releng-production-treestatus',
                'heroku_dyno_type': 'web',
                'url': 'https://treestatus.mozilla-releng.net',
                # TODO: this needs to be updated in mozilla-releng/build-cloud-tools
                'dns': 'kochi-31413.herokussl.com',
            },
        },
    },
    'shipit-bot-uplift': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploy': 'TASKCLUSTER_HOOK',
        'deploy_options': {
            'staging': {},
            'production': {},
        },
    },
    'shipit-code-coverage': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploy': 'TASKCLUSTER_HOOK',
        'deploy_options': {
            'staging': {},
            # 'production': {},
        },
    },
    'shipit-frontend': {
        'run': 'ELM',
        'run_options': {
            'port': 8010,
            'envs': {
                'bugzilla-url': 'https://bugzilla-dev.allizom.org',
            }
        },
        'requires': [
            'shipit-uplift',
        ],
        'deploy': 'S3',
        'deploy_options': {
            'staging': {
                's3_bucket': 'shipit-staging-frontend',
                'url': 'https://shipit.staging.mozilla-releng.net',
                'dns': 'd2ld4e8bl8yd1l.cloudfront.net.',
                'envs': {
                    'bugzilla-url': 'https://bugzilla.mozilla.org',
                },
                'csp': [
                    'https://login.taskcluster.net',
                    'https://auth.taskcluster.net',
                    'https://bugzilla.mozilla.org',
                ],
            },
            'production': {
                's3_bucket': 'shipit-production-frontend',
                'url': 'https://shipit.mozilla-releng.net',
                'dns': 'dve8yd1431ifz.cloudfront.net.',
                'envs': {
                    'bugzilla-url': 'https://bugzilla.mozilla.org',
                },
                'csp': [
                    'https://login.taskcluster.net',
                    'https://auth.taskcluster.net',
                    'https://bugzilla.mozilla.org',
                ],
            },
        },
    },
    'shipit-pipeline': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8012,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'shipit-staging-pipeline',
                'heroku_dyno_type': 'web',
                'url': 'https://pipeline.shipit.staging.mozilla-releng.net',
                'dns': 'pipeline.shipit.staging.mozilla-releng.net.herokudns.com',
            },
            # 'production': {
            #     'heroku_app': 'shipit-production-pipeline',
            #     'heroku_dyno_type': 'web',
            #     'url': 'https://pipeline.shipit.mozilla-releng.net',
            #     'dns': 'pipeline.shipit.mozilla-releng.net.herokudns.com',
            # },
        },
    },
    'shipit-pulse-listener': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'requires': [],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'shipit-staging-pulse-listener',
                'heroku_dyno_type': 'worker',
            },
            'production': {
                'heroku_app': 'shipit-production-pulse-listen',
                'heroku_dyno_type': 'worker',
            },
        },
    },
    'shipit-risk-assessment': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploy': 'TASKCLUSTER_HOOK',
        'deploy_options': {
            'staging': {},
            # 'production': {},
        },
    },
    'shipit-signoff': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8013,
            'envs': {
                'AUTH0_CLIENT_ID': 'XXX',
                'AUTH0_CLIENT_SECRET': 'YYY',
            }
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'shipit-staging-signoff',
                'heroku_dyno_type': 'web',
                'url': 'https://signoff.shipit.staging.mozilla-releng.net',
                'dns': 'signoff.shipit.staging.mozilla-releng.net.herokudns.com',
            },
            # 'production': {
            #     'heroku_app': 'shipit-production-signoff',
            #     'heroku_dyno_type': 'web',
            #     'url': 'https://signoff.shipit.mozilla-releng.net',
            #     'dns': 'signoff.shipit.mozilla-releng.net.herokudns.com',
            # },
        },
    },
    'shipit-static-analysis': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'deploy': 'TASKCLUSTER_HOOK',
        'deploy_options': {
            'staging': {},
            'production': {},
        },
    },
    'shipit-taskcluster': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8014,
        },
        'requires': [
            'postgresql',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'shipit-staging-taskcluster',
                'heroku_dyno_type': 'web',
                'url': 'https://taskcluster.shipit.staging.mozilla-releng.net',
                'dns': 'taskcluster.shipit.staging.mozilla-releng.net.herokudns.com',
            },
            # 'production': {
            #     'heroku_app': 'shipit-production-taskcluster',
            #     'heroku_dyno_type': 'web',
            #     'url': 'https://taskcluster.shipit.mozilla-releng.net',
            #     'dns': 'taskcluster.shipit.mozilla-releng.net.herokudns.com',
            # },
        },
    },
    'shipit-uplift': {
        'checks': [
            ('Checking code quality', 'flake8'),
            ('Running tests', 'pytest tests/'),
        ],
        'run': 'FLASK',
        'run_options': {
            'port': 8011,
        },
        'requires': [
            'postgresql',
            'redis',
        ],
        'deploy': 'HEROKU',
        'deploy_options': {
            'staging': {
                'heroku_app': 'shipit-staging-uplift',
                'heroku_dyno_type': 'web',
                'url': 'https://uplift.shipit.staging.mozilla-releng.net',
                'dns': 'uplift.shipit.staging.mozilla-releng.net.herokudns.com',
            },
            'production': {
                'heroku_app': 'shipit-production-uplift',
                'heroku_dyno_type': 'web',
                'url': 'https://uplift.shipit.mozilla-releng.net',
                'dns': 'uplift.shipit.mozilla-releng.net.herokudns.com',
            },
        },
    },
}
