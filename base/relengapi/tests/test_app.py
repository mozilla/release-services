# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from nose.tools import eq_
from relengapi.testing import TestContext


test_context = TestContext(reuse_app=True)


@test_context
def test_root(client):
    resp = client.get('/')
    eq_(resp.status_code, 200, resp.data)
    assert 'Releng API' in resp.data


@test_context
def test_versions(client):
    resp = client.get('/versions')
    eq_(resp.status_code, 200, resp.data)
    versions = json.loads(resp.data)
    assert 'base' in versions['result']['blueprints'], versions
