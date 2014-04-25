# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_, assert_raises
from flask.ext.principal import IdentityContext
from relengapi.lib.actions import Actions

def test_ActionElt_tuple_equivalence():
    "A action is equivalent to a tuple"
    actions = Actions()
    eq_(actions.foo.bar.bing, ('foo', 'bar', 'bing'))

def test_ActionElt_undoc_not_in_all():
    "Un-documented actions aren't in `actions.all`"
    actions = Actions()
    actions.a.b.c.d.doc("alphabetterjuice")
    ok_(actions.a.b.c.d in actions.all)
    ok_(actions.a.b.c not in actions.all)
    ok_(actions.a.b.never_mentioned not in actions.all)

def test_ActionElt_get():
    actions = Actions()
    actions.a.b.c.d.doc("alphabetterjuice")
    ok_(actions['a.b.c.d'] == actions.a.b.c.d)
    ok_(actions.get('a.b.c.d') == actions.a.b.c.d)
    ok_(actions.get('x.y') == None)
    ok_(actions.get('x.y', 'missing') == 'missing')

def test_ActionElt_undoc_KeyError():
    "Un-documented actions can't be looked up with []"
    actions = Actions()
    actions.a.b.c.d.doc("alphabetterjuice")
    assert_raises(KeyError, lambda: actions['a.b.c'])
    assert_raises(KeyError, lambda: actions['a.b.never_mentioned'])

def test_ActionElt_require():
    "Test the `.require` check"
    actions = Actions()
    actions.test.writer.doc("Test writer")
    ok_(isinstance(actions.test.writer.require(),
                   IdentityContext))
