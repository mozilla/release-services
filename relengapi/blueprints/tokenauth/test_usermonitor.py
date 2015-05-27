# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import mock

from nose.tools import eq_
from relengapi import p
from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth import usermonitor
from relengapi.blueprints.tokenauth.util import insert_usr
from relengapi.lib.testing.context import TestContext

p.test_usermonitor.a.doc("A")
A = p.test_usermonitor.a
p.test_usermonitor.b.doc("B")
B = p.test_usermonitor.b
p.test_usermonitor.c.doc("B")
C = p.test_usermonitor.c


test_context = TestContext(databases=['relengapi'])


@contextlib.contextmanager
def mocked_perms(permissions):
    with mock.patch('relengapi.lib.auth.perms_types.static.'
                    'StaticAuthz.get_user_permissions') as gup:
        def side_effect(user):
            if user in permissions:
                return set(permissions[user])
        gup.side_effect = side_effect
        yield


def assert_disabled(app, js, perms):
    perms_str = ', '.join(str(p) for p in perms)
    eq_(tables.Token.query.filter_by(id=2).first().disabled, True)
    js.log_message.assert_called_with("Disabling usr token #2 for user "
                                      "me@me.com with permissions " + perms_str)


def assert_enabled(app):
    eq_(tables.Token.query.filter_by(id=2).first().disabled, False)


def assert_reenabled(app, js, perms):
    assert_enabled(app)
    perms_str = ', '.join(str(p) for p in perms)
    js.log_message.assert_called_with("Re-enabling usr token #2 for user "
                                      "me@me.com with permissions " + perms_str)


@test_context
def test_monitor_users_disable_reduced_perms(app):
    """If the user's permissions are a subset of those for the token, disable"""
    with app.app_context():
        insert_usr(app, permissions=[A, B])
        with mocked_perms({'me@me.com': [A]}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_disabled(app, js, [A, B])


@test_context
def test_monitor_users_disable_changed_perms(app):
    """If the user's permissions are a, b and the token's are b, c, disable"""
    with app.app_context():
        insert_usr(app, permissions=[B, C])
        with mocked_perms({'me@me.com': [A, B]}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_disabled(app, js, [B, C])


@test_context
def test_monitor_users_disable_user_gone(app):
    """If the user is gone, disable"""
    with app.app_context():
        insert_usr(app, permissions=[A, B])
        with mocked_perms({}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_disabled(app, js, [A, B])


@test_context
def test_monitor_users_disable_user_gone_no_token_perms(app):
    """If the user is gone, disable even a token with no permissions."""
    with app.app_context():
        insert_usr(app, permissions=[])
        with mocked_perms({}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_disabled(app, js, [])


@test_context
def test_monitor_users_same_permissions(app):
    """If the user's permissions match the token's, leave it enabled"""
    with app.app_context():
        insert_usr(app, permissions=[A, B])
        with mocked_perms({'me@me.com': [A, B]}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_enabled(app)


@test_context
def test_monitor_users_ample_permissions(app):
    """If the user's permissions exceed the token's, leave it enabled"""
    with app.app_context():
        insert_usr(app, permissions=[A, B])
        with mocked_perms({'me@me.com': [A, B, C]}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_enabled(app)


@test_context
def test_monitor_users_reenable(app):
    """If the token is disabled and can be re-enabled, it is"""
    with app.app_context():
        insert_usr(app, permissions=[A, B], disabled=True)
        with mocked_perms({'me@me.com': [A, B, C]}):
            js = mock.Mock()
            usermonitor.monitor_users(js)
        assert_reenabled(app, js, [A, B])
