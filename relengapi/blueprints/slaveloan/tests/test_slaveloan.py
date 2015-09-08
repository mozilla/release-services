# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from flask import json
from nose.tools import eq_
from nose.tools import ok_
from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Humans
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines
from relengapi.lib import auth
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext
from relengapi.util import tz


def userperms(perms, email='me@example.com'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

test_context = TestContext(databases=['relengapi'], disable_login_view=True)
test_context_admin = TestContext(databases=['relengapi'],
                                 user=userperms([p.slaveloan.admin]),
                                 disable_login_view=True)
test_context_noperm_user = TestContext(databases=['relengapi'],
                                       user=userperms([], "noperm@mozilla.com"),
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

    # XXX History Tests
    # XXX ManualAction Tests
    # _ = (History, ManualActions)  # silence pyflakes
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

    @test_context_noperm_user
    def t3(path, app, client):
        with app.test_request_context():
            resp = client.get(path)
            eq_(resp.status_code, 403)

    for path in paths:
        yield t, path
        yield t2, path
        yield t3, path


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
    """Get the list of loans, does not include completed"""
    resp = client.get('/slaveloan/loans/')
    eq_(resp.status_code, 200)

    loans = json.loads(resp.data)['result']
    eq_(len(loans), 5)


@test_context_admin.specialize(db_setup=db_setup)
def test_get_loans_all(client):
    """Get the list of all loans"""
    resp = client.get('/slaveloan/loans/?all=1')
    eq_(resp.status_code, 200)

    loans = json.loads(resp.data)['result']
    eq_(len(loans), 6)


@test_context_admin.specialize(db_setup=db_setup)
def test_get_loans_specific(client):
    """Get a specific loan, by id"""
    resp = client.get('/slaveloan/loans/1')
    eq_(resp.status_code, 200)

    loan = json.loads(resp.data)['result']
    eq_(loan, {
        "bug_id": 1234001,
        "human": {
            "bugzilla_email": "user1@mozilla.com",
            "id": 1,
            "ldap_email": "user1@mozilla.com"
        },
        "id": 1,
        "machine": {
            "fqdn": "host1.mozilla.org",
            "id": 1,
            "ipaddress": "127.0.0.1"
        },
        "status": "ACTIVE"
    })


@test_context.specialize(db_setup=db_setup)
def test_complete_loan_requires_admin(client):
    "Getting a loan by ID currently requires admin privs"
    resp = client.open('/slaveloan/loans/1', method='DELETE')
    eq_(resp.status_code, 403)


@test_context_admin.specialize(db_setup=db_setup)
def test_complete_loan(client):
    "DELETEing a loan marks it as complete, regardless of what the prior value of status was"
    for i in (1, 2, 3):
        resp = client.open('/slaveloan/loans/%s' % i, method='DELETE')
        eq_(resp.status_code, 200)

        loan = json.loads(resp.data)['result']
        eq_(loan["status"], "COMPLETE")


@test_context_admin.specialize(db_setup=db_setup)
def test_complete_loan_history(app, client):
    "DELETEing a loan adds a history line"
    initial_time = tz.utcnow()
    with app.app_context():
        q = History.query
        q = q.filter(History.loan_id == 1)
        q = q.order_by(History.timestamp)
        eq_(0, len(q.all()))

        resp = client.open('/slaveloan/loans/1', method='DELETE')
        eq_(resp.status_code, 200)

        histories = q.all()
        eq_(1, len(q.all()))
        ok_(histories[0].timestamp > initial_time)


@test_context.specialize(db_setup=db_setup)
def test_new_loan_login_required(client):
    "Test that a post without a login fails"
    request = {}
    eq_(client.post_json('/slaveloan/loans/', request).status_code, 401)


@test_context_noperm_user.specialize(db_setup=db_setup)
def test_new_loan_request_missing_required(client):
    "Test that a loan request with missing required fields fail"
    request = {}
    eq_(client.post_json('/slaveloan/loans/', request).status_code, 400)
    request = {"ldap_email": "noperm@mozilla.com"}
    eq_(client.post_json('/slaveloan/loans/', request).status_code, 400)
    request = {"requested_slavetype": "invalid_slave"}
    eq_(client.post_json('/slaveloan/loans/', request).status_code, 400)


@test_context_noperm_user.specialize(db_setup=db_setup)
def test_new_loan_request_notme_unauthed(client):
    "Test that a loan request specifying a different ldap fails"
    request = {"ldap_email": "a_different_email@mozilla.com"}
    resp = client.post_json('/slaveloan/loans/', request)
    eq_(resp.status_code, 400)
    data = json.loads(resp.data)
    ok_("on behalf of others" in data["error"]["description"])


@test_context_noperm_user.specialize(db_setup=db_setup)
def test_new_loan_request_valid_works(client):
    "Test that a user with no permissions can issue a loan request"
    request = {"ldap_email": "noperm@mozilla.com",
               "requested_slavetype": "talos-mtnlion-r5"}
    with mock.patch("relengapi.blueprints.slaveloan.task_groups.chain") as mockedchain:
        resp = client.post_json('/slaveloan/loans/', request)
        eq_(resp.status_code, 200)
        data = json.loads(resp.data)
        expect = {
            u'bug_id': None,
            u'machine': None,
            u'status': u'PENDING',
            u'id': 7,
            u'human': {
                u'ldap_email': u'noperm@mozilla.com',
                u'bugzilla_email': u'noperm@mozilla.com',
                u'id': 5
            }
        }
        eq_(data["result"], expect)
        eq_(mockedchain().delay.called, True)
