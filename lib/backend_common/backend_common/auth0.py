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
from jose import jwt
import json
import hmac
import base64
import os
import tempfile

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


def get_token():
    if 'access_token' in flask.request.form:
        return flask.request.form['access_token']
    if 'access_token' in flask.request.args:
        return flask.request.args['access_token']

    auth = flask.request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected'
        }, 401)

    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with Bearer'},
            401)
    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found'},
            401)
    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be Bearer token'},
            401)

    token = parts[1]
    return token


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

    Side effects: flask.g gets the 'userinfo' and 'access_token' attributes
    containing the data from the response

    .. versionadded:: 1.0
    '''
    def wrapper(view_func):
        @functools.wraps(view_func)
        def decorated(*args, **kwargs):
            token = get_token()
            url = auth0.client_secrets.get(
                'userinfo_uri', 'https://{}/userinfo'.format(flask.current_app.config.get('AUTH_DOMAIN')))
            payload = {'access_token': token}
            response = requests.get(url, params=payload)

            # Because auth0 returns http 200 even if the token is invalid.
            if response.content == b'Unauthorized' or not response.ok:
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


def has_scopes(scopes, required_scopes):
    return set(scopes).issuperset(set(required_scopes))


@functools.lru_cache(maxsize=2048)
def get_jwks():
    jwks_url = 'https://{}/.well-known/jwks.json'.format(flask.current_app.config.get('AUTH_DOMAIN'))
    req = requests.get(jwks_url)
    req.raise_for_status()
    return req.json()


def verified_userinfo():
    jwks = get_jwks()
    token = get_token()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Invalid header. Use an RS256 signed JWT Access Token'},
            401)
    if unverified_header['alg'] == 'HS256':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Invalid header. Use an RS256 signed JWT Access Token'},
            401)
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=flask.current_app.config.get('AUTH_AUDIENCE'),
                issuer='https://{}/'.format(flask.current_app.config.get('AUTH_DOMAIN'))
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'token is expired'},
                401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'incorrect claims, please check the audience and issuer'},
                401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'},
                401)
    else:
        raise AuthError({
            'code': 'invalid_key',
            'description': 'Unable to find RSA key.'},
            401)


def requires_auth(view_func):

    @functools.wraps(view_func)
    def decorated(*args, **kwargs):
        flask.g.userinfo = verified_userinfo()
        flask.g.access_token = get_token()
        return view_func(*args, **kwargs)

    return decorated


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
