# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from nose.tools import eq_
from relengapi.blueprints.jacuzzi_allocator import Machine, Builder
from relengapi.testing import TestContext
        

def db_setup(app):
    session = app.db.session('jacuzzi_allocator')
    box1 = Machine(name='box1')
    session.add(box1)
    box2 = Machine(name='box2')
    session.add(box2)
    box3 = Machine(name='box3')
    session.add(box3)
    session.add(Builder(name='b1', machines=[box1, box2]))
    session.add(Builder(name='b2', machines=[box2, box3]))
    session.commit()

def db_teardown(app):
    engine = app.db.engine('jacuzzi_allocator')
    engine.execute('delete from machines')
    engine.execute('delete from builders')
    engine.execute('delete from allocations')

test_context = TestContext(databases=['jacuzzi_allocator'],
                           db_setup=db_setup,
                           db_teardown=db_teardown,
                           reuse_app=True)

@test_context
def test_all(client):
    rv = client.get('/jacuzzi-allocator/v1/allocated/all')
    eq_(json.loads(rv.data), {'machines': ['box1', 'box2', 'box3']})

@test_context
def test_machines(client):
    rv = client.get('/jacuzzi-allocator/v1/machines')
    eq_(json.loads(rv.data), {'machines': ['box1', 'box2', 'box3']})

@test_context
def test_machine(client):
    rv = client.get('/jacuzzi-allocator/v1/machines/box1')
    eq_(json.loads(rv.data), {'builders': ['b1']})
    rv = client.get('/jacuzzi-allocator/v1/machines/box2')
    eq_(json.loads(rv.data), {'builders': ['b1', 'b2']})

@test_context
def test_builders(client):
    rv = client.get('/jacuzzi-allocator/v1/builders')
    eq_(json.loads(rv.data), {'builders': ['b1', 'b2']})

@test_context
def test_builder(client):
    rv = client.get('/jacuzzi-allocator/v1/builders/b1')
    eq_(json.loads(rv.data), {'machines': ['box1', 'box2']})
    rv = client.get('/jacuzzi-allocator/v1/builders/b2')
    eq_(json.loads(rv.data), {'machines': ['box2', 'box3']})

