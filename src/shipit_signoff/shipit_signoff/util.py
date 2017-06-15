# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import tempfile


def is_key_present_in_list_of_dicts(key, list_of_dicts):
    return any(key in dict_ for dict_ in list_of_dicts)


def create_auth0_secrets_file(AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, APP_URL):
    secrets_file = tempfile.mkstemp()[1]
    with open(secrets_file, 'w+') as f:
        f.write(json.dumps({
            'web': {
                'auth_uri': 'https://auth.mozilla.auth0.com/authorize',
                'issuer': 'https://auth.mozilla.auth0.com/',
                'client_id': AUTH0_CLIENT_ID,
                'client_secret': AUTH0_CLIENT_SECRET,
                'redirect_uris': [
                    APP_URL + '/oidc_callback',
                ],
                'token_uri': 'https://auth.mozilla.auth0.com/oauth/token',
                'userinfo_uri': 'https://auth.mozilla.auth0.com/userinfo',
            }
        }))
    return secrets_file
