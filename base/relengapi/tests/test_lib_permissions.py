# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock
import werkzeug.exceptions
from nose.tools import eq_, ok_, assert_raises
from relengapi.lib import permissions


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


@mock.patch('relengapi.lib.permissions.current_user')
def test_require_can(current_user):
    "Test the `.require` method and function"
    perms = permissions.Permissions()
    perms.test.writer.doc("Test writer")
    perms.test.reader.doc("Test reader")
    perms.test.deleter.doc("Test deleter")

    current_user.permissions = set([perms.test.writer, perms.test.reader])

    @permissions.require(perms.test.writer, perms.test.reader)
    def func():
        return "ok"
    eq_(func(), "ok")

    @perms.test.writer.require()
    def meth():
        return "ok"
    eq_(meth(), "ok")

    @permissions.require(perms.test.writer, perms.test.deleter)
    def bad_func():
        return "ok"
    assert_raises(werkzeug.exceptions.Forbidden, bad_func)

    @perms.test.deleter.require()
    def bad_meth():
        return "ok"
    assert_raises(werkzeug.exceptions.Forbidden, bad_meth)

    # empty are invalid
    assert_raises(AssertionError, permissions.require)
    assert_raises(AssertionError, permissions.can)
