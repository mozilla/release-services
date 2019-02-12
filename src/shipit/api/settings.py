# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import os

import backend_common.auth0
import cli_common.taskcluster
import shipit_api.config

DEBUG = bool(os.environ.get('DEBUG', False))

# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY_BASE64',
    'DATABASE_URL',
    'AUTH_DOMAIN',
    'AUTH_CLIENT_ID',
    'AUTH_CLIENT_SECRET',
    'AUTH_REDIRECT_URI',
    'AUTH_AUDIENCE',
]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    shipit_api.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)

SECRET_KEY = base64.b64decode(secrets['SECRET_KEY_BASE64'])


# -- DATABASE -----------------------------------------------------------------
SQLALCHEMY_TRACK_MODIFICATIONS = False

if DEBUG:
    SQLALCHEMY_ECHO = True

# We require DATABASE_URL set by environment variables for branches deployed to Dockerflow.
if secrets['APP_CHANNEL'] in ('testing', 'staging', 'production'):
    if 'DATABASE_URL' not in os.environ:
        raise RuntimeError(f'DATABASE_URL has to be set as an environment variable, when '
                           f'APP_CHANNEL is set to {secrets["APP_CHANNEL"]}')
    else:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
else:
    SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']

# -- AUTH --------------------------------------------------------------------
OIDC_USER_INFO_ENABLED = True
args = [
    secrets['AUTH_CLIENT_ID'],
    secrets['AUTH_CLIENT_SECRET'],
    secrets['APP_URL'],
]
OIDC_CLIENT_SECRETS = backend_common.auth0.create_auth0_secrets_file(*args)

# XXX: scopes/groups are hardcoded for now
GROUPS = {
    'admin': [
        'asasaki@mozilla.com',
        'bhearsum@mozilla.com',
        'catlee@mozilla.com',
        'jlorenzo@mozilla.com',
        'jlund@mozilla.com',
        'jwood@mozilla.com',
        'mhentges@mozilla.com',
        'mtabara@mozilla.com',
        'nthomas@mozilla.com',
        'raliiev@mozilla.com',
        'rgarbas@mozilla.com',
        'sfraser@mozilla.com',
        'tprince@mozilla.com',
    ],
    'firefox-signoff': [
        'rkothari@mozilla.com',
        'ehenry@mozilla.com',
        'jcristau@mozilla.com',
        'pchevrel@mozilla.com',
        'sylvestre@debian.org',
        'rvandermeulen@mozilla.com',
    ],
    'thunderbird-signoff': [
        'vseerror@lehigh.edu',
        'mozilla@jorgk.com',
        'thunderbird@calypsoblue.org',
    ],
}

AUTH0_AUTH_SCOPES = {
    f'{shipit_api.config.SCOPE_PREFIX}/add_release': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/schedule_phase': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/abandon_release': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/sync_releases': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/rebuild_product_details': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/sync_release_datetimes': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/update_release_status': GROUPS['admin'],
    f'{shipit_api.config.SCOPE_PREFIX}/phase_signoff': GROUPS['admin'],
}

