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

from __future__ import absolute_import

import cli_common.log
from urllib.parse import urlencode
import time
import requests
import flask
import flask_oidc
import functools
import json
import hmac
import base64
import os

logger = cli_common.log.get_logger(__name__)
auth0 = flask_oidc.OpenIDConnect()

SETTINGS_REQUIRED = (
    'SECRET_KEY',
    'AUTH_CLIENT_ID',
    'AUTH_CLIENT_SECRET',
    'AUTH_REDIRECT_URI',
    'AUTH_DOMAIN',
)


def mozilla_accept_token(render_errors=True):
    '''
    Use this to decorate view functions that should accept OAuth2 tokens,
    this will most likely apply to API functions.

    Tokens are accepted as part of
    * the query URL (access_token value)
    * a POST form value (access_token)
    * the header Authorization: Bearer <token value>

    :param render_errors: Whether or not to eagerly render error objects
        as JSON API responses. Set to False to pass the error object back
        unmodified for later rendering.
    :type render_errors: bool

    Side effects: flask.g gets the 'userinfo' attribute containing the data
    from the response

    .. versionadded:: 1.0
    '''
    def wrapper(view_func):
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            token = None
            if flask.request.headers.get('Authorization', '').startswith('Bearer'):
                token = flask.request.headers['Authorization'].split(maxsplit=1)[
                    1].strip()
            if 'access_token' in flask.request.form:
                token = flask.request.form['access_token']
            elif 'access_token' in flask.request.args:
                token = flask.request.args['access_token']

            url = auth0.client_secrets.get(
                'userinfo_uri', 'https://auth.mozilla.auth0.com/userinfo')
            payload = {'access_token': token}
            response = requests.get(url, params=payload)

            # Because auth0 returns http 200 even if the token is invalid.
            if response.content == b'Unauthorized':
                response_body = {'error': 'invalid_token',
                                 'error_description': str(response.content, 'utf-8')}
                if render_errors:
                    response_body = json.dumps(response_body)
                return response_body, 401, {'WWW-Authenticate': 'Bearer'}

            # store response.content for later
            flask.g.userinfo = json.loads(str(response.content, 'utf-8'))
            # g.oidc_id_token = token # requires a specific format
            flask.g.access_token = token

            return view_func(*args, **kwargs)

        return decorated
    return wrapper


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
        'scope': 'full-user-credentials openid',
        'response_type': 'code',
        'client_id': flask.current_app.config.get('AUTH_CLIENT_ID'),
        'redirect_uri': flask.current_app.config.get('AUTH_REDIRECT_URI'),
        'state': build_state(),
    }
    return 'https://{}/authorize?{}'.format(
        flask.current_app.config.get('AUTH_DOMAIN'),
        urlencode(params),
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
    auth0.init_app(app)
    return auth0
