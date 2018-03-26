# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import base64
import os
import cli_common.taskcluster
import shipit_workflow.config
import backend_common.auth0

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
    shipit_workflow.config.PROJECT_NAME,
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

# -- AUTH --------------------------------------------------------------------
OIDC_USER_INFO_ENABLED = True
args = [
    secrets['AUTH_CLIENT_ID'],
    secrets['AUTH_CLIENT_SECRET'],
    secrets['APP_URL'],
]
OIDC_CLIENT_SECRETS = backend_common.auth0.create_auth0_secrets_file(*args)
