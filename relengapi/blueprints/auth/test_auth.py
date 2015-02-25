# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from nose.tools import eq_
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext

test_context = TestContext(reuse_app=True)


@test_context
def test_root(client):
    """The auth root loads a page"""
    resp = client.get('/auth/')
    eq_(resp.status_code, 200, resp.data)
    assert 'You have the following permissions' in resp.data, resp.data


p.test_auth.aaa.doc('test_auth test perm')


@test_context.specialize(perms=[p.test_auth.aaa])
def test_permissions(client):
    """The /permissions API endpoint returns the user's permissions"""
    resp = client.get('/auth/permissions')
    eq_(resp.status_code, 200, resp.data)
    eq_(json.loads(resp.data)['result'], [
        {'doc': 'test_auth test perm', 'name': 'test_auth.aaa'},
    ])
