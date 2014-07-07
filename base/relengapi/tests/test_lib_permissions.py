# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock
import werkzeug.exceptions
from flask.ext.login import current_user
from flask.ext.login import login_user
from nose.tools import eq_, ok_, assert_raises
from relengapi.lib import permissions
from relengapi.testing import TestContext
from relengapi.lib import auth


def test_Permission_tuple_equivalence():
    "A permission is equivalent to a tuple"
    perms = permissions.Permissions()
    eq_(perms.foo.bar.bing, ('foo', 'bar', 'bing'))


def test_Permission_undoc_not_in_all():
    "Un-documented permissions aren't in `perms.all`"
    perms = permissions.Permissions()
    perms.a.b.c.d.doc("alphabetterjuice")
    ok_(perms.a.b.c.d in perms.all)
    ok_(perms.a.b.c not in perms.all)
    ok_(perms.a.b.never_mentioned not in perms.all)


def test_Permission_get():
    perms = permissions.Permissions()
    perms.a.b.c.d.doc("alphabetterjuice")
    ok_(perms['a.b.c.d'] == perms.a.b.c.d)
    ok_(perms.get('a.b.c.d') == perms.a.b.c.d)
    ok_(perms.get('x.y') is None)
    ok_(perms.get('x.y', 'missing') == 'missing')


def test_Permission_undoc_KeyError():
    "Un-documented perms can't be looked up with []"
    perms = permissions.Permissions()
    perms.a.b.c.d.doc("alphabetterjuice")
    assert_raises(KeyError, lambda: perms['a.b.c'])
    assert_raises(KeyError, lambda: perms['a.b.never_mentioned'])


class TestUser(auth.BaseUser):

    anonymous = False
    name = 'test'
    permissions = set()
    authenticated_email = 'test'

    def get_id(self):
        return 'test'


@TestContext()
def test_require_can(app):
    "Test the `.require` method and function"
    perms = permissions.Permissions()
    perms.test.writer.doc("Test writer")
    perms.test.reader.doc("Test reader")
    perms.test.deleter.doc("Test deleter")

    with app.test_request_context():
        login_user(TestUser())
        current_user.permissions = set([perms.test.writer, perms.test.reader])

        @permissions.require(perms.test.writer, perms.test.reader)
        def func():
            return "ok"
        eq_(func(), "ok")

        @perms.test.writer.require()
        def meth():
            return "ok"
        eq_(meth(), "ok")

        with mock.patch('relengapi.util.is_browser') as is_browser:
            # without a browser, failing requirements means 403
            is_browser.return_value = False

            @permissions.require(perms.test.writer, perms.test.deleter)
            def bad_func_rest():
                return "ok"
            assert_raises(werkzeug.exceptions.Forbidden, bad_func_rest)

            @perms.test.deleter.require()
            def bad_meth_rest():
                return "ok"
            assert_raises(werkzeug.exceptions.Forbidden, bad_meth_rest)

            # with a browser, they return 302's
            is_browser.return_value = True

            @permissions.require(perms.test.writer, perms.test.deleter)
            def bad_func_browser():
                return "ok"
            eq_(bad_func_browser().status_code, 302)

            @perms.test.deleter.require()
            def bad_meth_browser():
                return "ok"
            eq_(bad_meth_browser().status_code, 302)

        # empty are invalid
        assert_raises(AssertionError, permissions.require)
        assert_raises(AssertionError, permissions.can)
