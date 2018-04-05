# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

import backend_common


@pytest.fixture(scope='session')
def app():
    '''Load shipit_workflow in test mode
    '''
    import shipit_workflow

    config = backend_common.testing.get_app_config({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'AUTH_CLIENT_ID': 'dummy_id',
        'AUTH_CLIENT_SECRET': 'dummy_secret',
        'AUTH_DOMAIN': 'auth.localhost',
        'AUTH_REDIRECT_URI': 'http://localhost/login',
        'OIDC_USER_INFO_ENABLED': True,
        'OIDC_CLIENT_SECRETS': os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
    })
    app = shipit_workflow.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
