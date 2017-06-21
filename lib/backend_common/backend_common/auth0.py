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
import flask
import flask_oidc
import functools
import json
import requests


logger = cli_common.log.get_logger(__name__)
auth0 = flask_oidc.OpenIDConnect()


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


def init_app(app):
    if app.config.get('SECRET_KEY') is None:
        raise Exception('When using `auth0` extention you need to specify SECRET_KEY.')
    auth0.init_app(app)
    return auth0
