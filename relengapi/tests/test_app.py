# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import relengapi.app

from nose.tools import eq_
from relengapi.lib.testing.context import TestContext


test_context = TestContext(reuse_app=True)


@test_context
def test_root(client):
    """The root page loads with 200 OK"""
    resp = client.get('/')
    eq_(resp.status_code, 200, resp.data)
    assert 'Releng API' in resp.data


def test_create_app_no_env():
    """Creating an application with no $RELENGAPI_SETTINGS set
    succeeds (using default values)"""
    # the test harness removes this env variable; just verify here
    assert 'RELENGAPI_SETTINGS' not in os.environ
    app = relengapi.app.create_app()
    with app.test_client() as client:
        eq_(client.get('/versions').status_code, 200)


@test_context
def test_versions(client):
    """The /versions API method returns information about the base
    blueprint, at least"""
    resp = client.get('/versions')
    eq_(resp.status_code, 200, resp.data)
    versions = json.loads(resp.data)
    assert 'base' in versions['result']['blueprints'], versions
