# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

'''Configure a mock application to run queries against
'''

import flask
import flask_login
import os.path
import pytest


@pytest.fixture(scope='session')
def app():
    '''
    Build an app with an authenticated dummy api
    '''
    import backend_common

    # Use unique auth instance
    config = backend_common.testing.get_app_config({
        'OIDC_CLIENT_SECRETS': os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
        'OIDC_RESOURCE_SERVER_ONLY': True,
        'APP_TEMPLATES_FOLDER': '',
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    app = backend_common.create_app(
        'test',
        extensions=backend_common.EXTENSIONS,
        config=config,
    )

    @app.route('/')
    def index():
        return app.response_class('OK')

    @app.route('/test-auth-login')
    @backend_common.auth.auth.require_login
    def logged_in():
        data = {
            'auth': True,
            'user': flask_login.current_user.get_id(),
            # permissions is a set, not serializable
            'scopes': list(flask_login.current_user.permissions),
        }
        return flask.jsonify(data)

    @app.route('/test-auth-scopes')
    @backend_common.auth.auth.require_scopes([
        ['project/test/A', 'project/test/B'],
        ['project/test-admin/*'],
    ])
    def scopes():
        return app.response_class('Your scopes are ok.')

    @app.route('/test-auth0-userinfo')
    @backend_common.auth0.mozilla_accept_token()
    def auth0_token():
        return app.response_class('OK')

    # Add fake swagger url, used by redirect
    app.api.swagger_url = '/'

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
