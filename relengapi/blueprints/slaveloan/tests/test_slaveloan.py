# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Humans
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines
from relengapi.blueprints.slaveloan.model import ManualActions
from relengapi.lib import auth
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext


def userperms(perms, email='me@example.com'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

test_context = TestContext(disable_login_view=True)
test_context_admin = TestContext(databases=['relengapi'],
                                 user=userperms([p.slaveloan.admin]),
                                 disable_login_view=True)


def db_setup(app):
    session = app.db.session('relengapi')
    machines = []
    for m in (("127.0.0.1", "host1.mozilla.org"),
              ("127.0.0.2", "host2.mozilla.org"),
              ("127.0.0.3", "host3.mozilla.org"),
              ("127.0.0.4", "host4.mozilla.org"),
              ("127.0.0.5", "host5.mozilla.org")):
        machines.append(Machines(ipaddress=m[0], fqdn=m[1]))
    session.add_all(machines)

    humans = []
    for u in (("user1@mozilla.com", "user1@mozilla.com"),
              ("user2@mozilla.com", "user2@mozilla.com"),
              ("user3@mozilla.com", "user3@allizom.com"),
              ("user4@mozilla.com", "user4@mozilla.com")):
        humans.append(Humans(ldap=u[0], bugzilla=u[1]))
    session.add_all(humans)

    loans = []
    for l in (  # status, bug, machine, human
             ("ACTIVE", 1234001, machines[0], humans[0]),
             ("COMPLETE", 1234002, machines[1], humans[1]),
             ("PENDING", 1234003, machines[2], humans[2]),
             ("ACTIVE", 1234004, machines[3], humans[0]),
             ("ACTIVE", 1234005, machines[4], humans[1]),
             ("PENDING", 1234006, None, humans[0])):
        loans.append(Loans(status=l[0], bug_id=l[1], machine=l[2], human=l[3]))
    session.add_all(loans)
    if 0:
        # XXX History Tests
        # XXX ManualAction Tests
        _ = (History, ManualActions)  # silence pyflakes
    session.commit()


@test_context
def test_ui_root(client):
    "The root of the blueprint is not accessible without login"
    rv = client.get('/slaveloan/')
    eq_(rv.status_code, 401)


def test_ui_admin_required():
    "Test that admin perm is required for endpoints"
    paths = [
        '/slaveloan/admin/',
        '/slaveloan/details/2',
        '/slaveloan/manual_actions',
    ]

    @test_context
    def t(path, app, client):
        with app.test_request_context():
            resp = client.get(path)
            eq_(resp.status_code, 401)

    @test_context_admin
    def t2(path, app, client):
        with app.test_request_context():
            resp = client.get(path)
            eq_(resp.status_code, 200)

    for path in paths:
        yield t, path
        yield t2, path


@test_context
def test_machine_classes(client):
    "Test that someone not logged in can access the slave class mapping"
    rv = client.get('/slaveloan/machine/classes')
    eq_(rv.status_code, 200)


@test_context_admin
def test_manual_actions_all(client):
    "Test that the query arg all is accepted"
    rv = client.get('/slaveloan/manual_actions?all=1')
    eq_(rv.status_code, 200)


@test_context_admin
def test_manual_actions_loan(client):
    "Test that the query arg loan_id is accepted"
    rv = client.get('/slaveloan/manual_actions?loan_id=2')
    eq_(rv.status_code, 200)


@test_context_admin
def test_get_loans_raises(client):
    """Getting a list of loans with ?all=<bad_argument> should fail"""
    for arg in (2, -1):
        rv = client.get('/slaveloan/loans/?all=%s' % arg)
        eq_(rv.status_code, 400)


@test_context_admin.specialize(db_setup=db_setup)
def test_get_loans_default(client):
    """Get the list of loans, does not include pending"""
    rv = client.get('/slaveloan/loans/')
    eq_(rv.status_code, 200)

    loans = json.loads(resp.data)['result']
    eq_(len(loans), 5)


@test_context_admin.specialize(db_setup=db_setup)
def test_get_loans_default(client):
    """Get the list of loans, does not include pending"""
    rv = client.get('/slaveloan/loans/?all=1')
    eq_(rv.status_code, 200)

    loans = json.loads(resp.data)['result']
    eq_(len(loans), 6)
