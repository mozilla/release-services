# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib import auth
from relengapi.lib.permissions import p
from relengapi.lib.testing.context import TestContext


def userperms(perms, email='me@example.com'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

test_context = TestContext()
test_context_admin = TestContext(databases=['relengapi'],
                                 user=userperms([p.slaveloan.admin]))


@test_context
def test_ui_root(client):
    "The root of the blueprint is accessible without login"
    rv = client.get('/slaveloan/')
    eq_(rv.status_code, 200)


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
            eq_(resp.status_code, 403)

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
