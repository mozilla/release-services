# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import pytest
import os

import backend_common


@pytest.fixture(scope='function')
def app():
    '''Load shipit_signoff in test mode
    '''
    import shipit_signoff
    import shipit_signoff.util

    config = backend_common.testing.get_app_config({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': os.urandom(24),
        'OIDC_USER_INFO_ENABLED': True,
        'OIDC_CLIENT_SECRETS': shipit_signoff.util.create_auth0_secrets_file(
            '123',
            '123',
            'https://APP_URL',
        ),
        'BALROG_API_ROOT': 'https://balrog/api',
        'BALROG_USERNAME': 'balrogadmin',
        'BALROG_PASSWORD': 'balrogadmin',
    })
    app = shipit_signoff.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
