# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import cli_common.taskcluster
import shipit_signoff.config
import shipit_signoff.util


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY',
    'DATABASE_URL',
    'APP_URL',
    'AUTH0_CLIENT_ID',
    'AUTH0_CLIENT_SECRET',

]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    shipit_signoff.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)


# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False


# -- AUTH0 --------------------------------------------------------------------


SECRET_KEY = os.urandom(24)
# OIDC_CALLBACK_ROUTE='/redirect_url'
OIDC_USER_INFO_ENABLED = True
OIDC_CLIENT_SECRETS = shipit_signoff.util.create_auth0_secrets_file(
    secrets['AUTH0_CLIENT_ID'],
    secrets['AUTH0_CLIENT_SECRET'],
    secrets['APP_URL'],
)
