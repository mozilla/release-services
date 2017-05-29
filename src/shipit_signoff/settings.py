# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import os
import tempfile
import cli_common.taskcluster
import shipit_signoff.config


DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'DATABASE_URL',
    'APP_URL',
    'AUTH0_CLIENT_ID',
    'AUTH0_CLIENT_SECRET',

]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    shipit_signoff.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required},
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
OIDC_CLIENT_SECRETS = tempfile.mkstemp()[1]


with open(OIDC_CLIENT_SECRETS, 'w+') as f:
    f.write(json.dumps({
        'web': {
            'auth_uri': 'https://auth.mozilla.auth0.com/authorize',
            'issuer': 'https://auth.mozilla.auth0.com/',
            'client_id': secrets['AUTH0_CLIENT_ID'],
            'client_secret': secrets['AUTH0_CLIENT_SECRET'],
            'redirect_uris': [
                secrets['APP_URL'] + '/oidc_callback',
            ],
            'token_uri': 'https://auth.mozilla.auth0.com/oauth/token',
            'userinfo_uri': 'https://auth.mozilla.auth0.com/userinfo',
        }
    }))
