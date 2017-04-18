# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import os
import tempfile


APP_URL = os.environ.get('APP_URL')

if not APP_URL:
    raise Exception("You need to specify APP_URL variable.")


SWAGGER_BASE_URL = os.environ.get('SWAGGER_BASE_URL')


# -- DATABASE -----------------------------------------------------------------

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise Exception("You need to specify DATABASE_URL variable.")
#
if not DATABASE_URL.startswith('postgresql://'):
    raise Exception('Shipit dashboard needs a postgresql:// DATABASE_URL')


SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False


# -- AUTH0 --------------------------------------------------------------------


AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')

if not AUTH0_CLIENT_ID:
    raise Exception("You need to specify AUTH0_CLIENT_ID variable.")

if not AUTH0_CLIENT_SECRET:
    raise Exception("You need to specify AUTH0_CLIENT_SECRET variable.")


SECRET_KEY = os.urandom(24)
# OIDC_CALLBACK_ROUTE='/redirect_url'
OIDC_USER_INFO_ENABLED = True
OIDC_CLIENT_SECRETS = tempfile.mkstemp()[1]


with open(OIDC_CLIENT_SECRETS, "w+") as f:
    f.write(json.dumps({
        "web": {
            "auth_uri": "https://auth.mozilla.auth0.com/authorize",
            "issuer": "https://auth.mozilla.auth0.com/",
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "redirect_uris": [
                APP_URL + "/oidc_callback",
            ],
            "token_uri": "https://auth.mozilla.auth0.com/oauth/token",
            "userinfo_uri": "https://auth.mozilla.auth0.com/userinfo",
        }
    }))
