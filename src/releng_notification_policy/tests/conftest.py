# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import pytest

import backend_common


@pytest.fixture(scope='session')
def app():
    import releng_notification_policy

    config = backend_common.testing.get_app_config({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'RELENG_NOTIFICATION_IDENTITY_ENDPOINT': 'https://fake_endpoint.mozilla-releng.net',
        'TASKCLUSTER_CLIENT_ID': 'something',
        'TASKCLUSTER_ACCESS_TOKEN': 'something',
    })
    app = releng_notification_policy.create_app(config)

    with app.app_context():
        backend_common.testing.configure_app(app)
        yield app
