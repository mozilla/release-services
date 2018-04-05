# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

import backend_common


@pytest.fixture(scope='session')
def app():
    '''Load releng_tooltool in test mode
    '''
    import releng_tooltool

    config = backend_common.testing.get_app_config({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'S3_REGIONS': dict(),
        'S3_REGIONS_ACCESS_KEY_ID': '123',
        'S3_REGIONS_SECRET_ACCESS_KEY': '123',
    })
    app = releng_tooltool.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
