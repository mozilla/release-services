# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Provide auth0 / OpenID Connect protection for API endpoints.

accept_token will take an oauth2 access_token provided by auth0 and
user the userinfo endpoint to validate it. This is because the token
info endpoint used by the Flask-OIDC accept_token wrapper has some
issues with validating tokens for certain application types.
"""

from __future__ import absolute_import
from functools import wraps
import json
import flask_oidc
from flask import g, request
import requests

auth0 = flask_oidc.OpenIDConnect()


def accept_token(render_errors=True):
    """
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
    """
    def wrapper(view_func):
        @wraps(view_func)
        def decorated(*args, **kwargs):
            token = None
            if request.headers.get('Authorization', '').startswith('Bearer'):
                token = request.headers['Authorization'].split(maxsplit=1)[
                    1].strip()
            if 'access_token' in request.form:
                token = request.form['access_token']
            elif 'access_token' in request.args:
                token = request.args['access_token']

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

            # store response.content for later?
            g.userinfo = json.loads(response.content)

            return view_func(*args, **kwargs)

        return decorated
    return wrapper


def init_app(app):
    auth0.init_app(app)
    return auth0
