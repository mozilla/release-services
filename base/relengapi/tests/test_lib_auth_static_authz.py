# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import relengapi.app

from nose.tools import assert_raises
from nose.tools import eq_
from relengapi import p
from relengapi.lib import auth
from relengapi.lib.auth import static_authz

p.test_static.foo.doc("Foo")
p.test_static.bar.doc("Bar")

perm_map = {
    'foo@co.com': ['test_static.foo'],
    'bar@co.com': ['test_static.foo', 'test_static.bar'],
}


def test_bad_config():
    bad_config = {
        'RELENGAPI_PERMISSIONS': {
            'type': 'static',
            'permissions': {
                'foo@co.com': ['no.such.foo'],
            },
        },
    }
    assert_raises(RuntimeError,
                  lambda: relengapi.app.create_app(
                      test_config=bad_config))


def test_on_permissions_stale_not_user():
    user = auth.HumanUser('jimmy@co.com')
    permissions = set()
    static_authz.on_permissions_stale(perm_map, 'sender', user, permissions)
    eq_(permissions, set())


def test_on_permissions_stale():
    user = auth.HumanUser('bar@co.com')
    permissions = set()
    static_authz.on_permissions_stale(perm_map, 'sender', user, permissions)
    eq_(permissions, set(
        [p.test_static.foo, p.test_static.bar]))
