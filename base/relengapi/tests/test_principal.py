# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_, assert_raises
from flask.ext.principal import IdentityContext
from relengapi import principal

def test_roles_attribute():
    "The `principal` package hsa a `roles` attribute"
    ok_(isinstance(principal.roles, principal.RootRoleElt))

def test_RoleElt_tuple_equivalence():
    "A role is equivalent to a tuple"
    roles = principal.RootRoleElt()
    eq_(roles.foo.bar.bing, ('foo', 'bar', 'bing'))

def test_RoleElt_undoc_not_in_all():
    "Un-documented roles aren't in `roles.all`"
    roles = principal.RootRoleElt()
    roles.a.b.c.d.doc("alphabetterjuice")
    ok_(roles.a.b.c.d in roles.all)
    ok_(roles.a.b.c not in roles.all)
    ok_(roles.a.b.never_mentioned not in roles.all)

def test_RoleElt_undoc_KeyError():
    "Un-documented roles can't be looked up with []"
    roles = principal.RootRoleElt()
    roles.a.b.c.d.doc("alphabetterjuice")
    ok_(roles['a.b.c.d'] == roles.a.b.c.d)
    assert_raises(KeyError, lambda: roles['a.b.c'])
    assert_raises(KeyError, lambda: roles['a.b.never_mentioned'])

def test_RoleElt_require():
    "Test the `.require` check"
    roles = principal.RootRoleElt()
    roles.test.writer.doc("Test writer")
    ok_(isinstance(roles.test.writer.require(),
                   IdentityContext))
