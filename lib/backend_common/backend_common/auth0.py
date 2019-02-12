# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''
Provide auth0 / OpenID Connect protection for API endpoints.

accept_token will take an oauth2 access_token provided by auth0 and
user the userinfo endpoint to validate it. This is because the token
info endpoint used by the Flask-OIDC accept_token wrapper has some
issues with validating tokens for certain application types.
'''

import base64
import functools
import hmac
import json
import os
import tempfile
import time
import urllib.parse

import flask
import flask_oidc
import jose.jwt
import requests

import backend_common.dockerflow
import cli_common.log

logger = cli_common.log.get_logger(__name__)
auth0 = flask_oidc.OpenIDConnect()

SETTINGS_REQUIRED = (
    'SECRET_KEY',
    'AUTH_CLIENT_ID',
    'AUTH_CLIENT_SECRET',
    'AUTH_REDIRECT_URI',
    'AUTH_DOMAIN',
)


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def handle_auth_error(e):
    response = flask.jsonify(e.error)
    response.status_code = e.status_code
    return response


def build_state(seed=None, size=8):
    '''
    Build a unique opaque value, used by Auth0
    as XSRF protection, using HMAC algorithm
    '''
    if seed is None:
        seed = os.urandom(size)
    else:
        assert isinstance(seed, bytes)
    assert len(seed) == size

    h = hmac.new(
        msg=seed,
        key=flask.current_app.config.get('SECRET_KEY'),
    )
    return base64.urlsafe_b64encode(b''.join([seed, h.digest()]))


def check_state(state, size=8):
    '''
    Check a previously created state value is valid
    for this website
    '''
    data = base64.urlsafe_b64decode(state)
    return hmac.compare_digest(
        state.encode('utf-8'),
        build_state(data[:size], size),
    )


def auth0_login():
    '''
    API Endpoint: Build Url to login on Auth0 server
    '''
    params = {
        'audience': 'login.taskcluster.net',
        'scope': 'taskcluster-credentials openid',
        'response_type': 'code',
        'client_id': flask.current_app.config.get('AUTH_CLIENT_ID'),
        'redirect_uri': flask.current_app.config.get('AUTH_REDIRECT_URI'),
        'state': build_state(),
    }
    return 'https://{}/authorize?{}'.format(
        flask.current_app.config.get('AUTH_DOMAIN'),
        urllib.parse.urlencode(params),
    )


def auth0_check():
    '''
    Echange auth0 login code for long lasting tokens
    access_token & id_token
    '''
    # Check state
    state = flask.request.json.get('state')
    assert state is not None, \
        'Missing state in payload'
    assert check_state(state), \
        'Invalid state value'

    code = flask.request.json.get('code')
    assert code is not None, \
        'Missing code in payload'

    # Exchange code for tokens
    url = 'https://{}/oauth/token'.format(
        flask.current_app.config.get('AUTH_DOMAIN')
    )
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': flask.current_app.config.get('AUTH_CLIENT_ID'),
        'client_secret': flask.current_app.config.get('AUTH_CLIENT_SECRET'),
        'redirect_uri': flask.current_app.config.get('AUTH_REDIRECT_URI'),
    }
    auth = requests.post(url, payload)
    if not auth.ok:
        # Forward error
        return auth.json(), auth.status_code

    # Export values
    data = auth.json()
    return {
        'expires': int(time.time()) + data['expires_in'],
        'access_token': data['access_token'],
        'id_token': data['id_token'],
    }


def init_app(app):
    for setting in SETTINGS_REQUIRED:
        if app.config.get(setting) is None:
            raise Exception('When using `auth0` extention you need to specify {}.'.format(setting))  # noqa
    app.register_error_handler(AuthError, handle_auth_error)
    auth0.init_app(app)
    return auth0


def create_auth0_secrets_file(AUTH_CLIENT_ID, AUTH_CLIENT_SECRET, APP_URL,
                              USERINFO_URI='https://auth.mozilla.auth0.com/userinfo'):
    secrets_file = tempfile.mkstemp()[1]
    with open(secrets_file, 'w+') as f:
        f.write(json.dumps({
            'web': {
                'auth_uri': 'https://auth.mozilla.auth0.com/authorize',
                'issuer': 'https://auth.mozilla.auth0.com/',
                'client_id': AUTH_CLIENT_ID,
                'client_secret': AUTH_CLIENT_SECRET,
                'redirect_uris': [
                    APP_URL + '/oidc_callback',
                ],
                'token_uri': 'https://auth.mozilla.auth0.com/oauth/token',
                'userinfo_uri': USERINFO_URI,
            }
        }))
    return secrets_file


def app_heartbeat():
    try:
        r = requests.get('https://auth.mozilla.auth0.com/test')
        assert 'clock' in r.json()
    except Exception as e:
        logger.exception(e)
        raise backend_common.dockerflow.HeartbeatException('Cannot connect to the mozilla auth0 service.')
