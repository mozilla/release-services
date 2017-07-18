# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import base64
import os
import cli_common.taskcluster
import releng_treestatus.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY_BASE64',
    'DATABASE_URL'
]

if not DEBUG:
    required += [
        'REDIS_URL',
        'PULSE_USER',
        'PULSE_TREESTATUS_EXCHANGE',
        'PULSE_TREESTATUS_EXCHANGE',
        'PULSE_USE_SSL',
        'PULSE_CONNECTION_TIMEOUT',
        'PULSE_HOST',
        'PULSE_PORT',
        'PULSE_USER',
        'PULSE_PASSWORD',
        'PULSE_VIRTUAL_HOST',
    ]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    releng_treestatus.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)

SECRET_KEY = base64.b64decode(secrets['SECRET_KEY_BASE64'])


# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False


# -- CACHE --------------------------------------------------------------------

CACHE = {
    x: os.environ.get(x)
    for x in os.environ.keys()
    if x.startswith('CACHE_')
}

if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5
else:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = float(CACHE['CACHE_DEFAULT_TIMEOUT'])

if 'CACHE_KEY_PREFIX' not in CACHE:
    CACHE['CACHE_KEY_PREFIX'] = releng_treestatus.config.PROJECT_NAME + '-'

if not DEBUG:
    CACHE['CACHE_TYPE'] = 'redis'
    CACHE['CACHE_REDIS_URL'] = secrets['REDIS_URL']


# -- PULSE --------------------------------------------------------------------
#
# Only used in production.
#

PULSE_TREESTATUS_ENABLE = False

if not DEBUG:
    PULSE_TREESTATUS_ENABLE = True
    PULSE_TREESTATUS_EXCHANGE = secrets['PULSE_TREESTATUS_EXCHANGE']
    PULSE_USE_SSL = bool(secrets['PULSE_USE_SSL'])
    PULSE_CONNECTION_TIMEOUT = int(secrets['PULSE_CONNECTION_TIMEOUT'])
    PULSE_HOST = secrets['PULSE_HOST']
    PULSE_PORT = int(secrets['PULSE_PORT'])
    PULSE_USER = secrets['PULSE_USER']
    PULSE_PASSWORD = secrets['PULSE_PASSWORD']
    PULSE_VIRTUAL_HOST = secrets['PULSE_VIRTUAL_HOST']
