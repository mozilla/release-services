# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import base64
import os
import cli_common.taskcluster
import releng_channel_status.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

# required = [
#     'SECRET_KEY_BASE64'
# ]

# secrets = cli_common.taskcluster.get_secrets(
#     os.environ.get('TASKCLUSTER_SECRET'),
#     releng_channel_status.config.PROJECT_NAME,
#     required=required,
#     existing={x: os.environ.get(x) for x in required if x in os.environ},
#     taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
#     taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
# )

# locals().update(secrets)

# SECRET_KEY = base64.b64decode(secrets['SECRET_KEY_BASE64'])

# -- CACHE --------------------------------------------------------------------

# CACHE = {
#     x: os.environ.get(x)
#     for x in os.environ.keys()
#     if x.startswith('CACHE_')
# }

# if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
#     CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5
# else:
#     CACHE['CACHE_DEFAULT_TIMEOUT'] = float(CACHE['CACHE_DEFAULT_TIMEOUT'])

# if 'CACHE_KEY_PREFIX' not in CACHE:
#     CACHE['CACHE_KEY_PREFIX'] = releng_channel_status.config.PROJECT_NAME + '-'

# if not DEBUG:
#     CACHE['CACHE_TYPE'] = 'redis'
#     CACHE['CACHE_REDIS_URL'] = secrets['REDIS_URL']


# -- Balrog Public API settings -----------------------------------------------
BALROG_API_URL = 'http://172.18.0.3:9090/api/v1/'
RULES_ENDPOINT = 'rules'
SINGLE_RULE_ENDPOINT = 'rules/{alias}'
RELEASE_ENDPOINT = 'releases/{release}'
DEFAULT_ALIAS = 'firefox-nightly'
UPDATE_MAPPINGS = ['Firefox-mozilla-central-nightly-latest']
DEFAULT_LOCALE = 'en-US'
DEFAULT_PLATFORM = 'Linux_x86_64-gcc3'