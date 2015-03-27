# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib.testing.context import TestContext


def userperms(perms, email='me@example.com'):
    u = auth.HumanUser(email)
    u._permissions = set(perms)
    return u

test_context = TestContext()
test_context_admin = TestContext(databases=['relengapi'],
                                 user=userperms([p.slaveloan.admin]))


@test_context
def test_root(client):
    "The root of the blueprint is accessible without login"
    rv = client.get('/slaveloan/')
    eq_(rv.status_code, 200)


@test_context
def test_admin_ui_not_authorized(client):
    "Test that an unlogged in user can't access the admin ui"
    rv = client.get('/slaveloan/admin')
    eq_(rv.status_code, 301)


@test_context_admin
def test_admin_ui_authorized(client):
    "Test that an admin can access the admin ui"
    rv = client.get('/slaveloan/admin')
    eq_(rv.status_code, 200)


@test_context
def test_details_ui_not_authorized(client):
    "Test that an logged out user can't access the loan details ui"
    rv = client.get('/slaveloan/details/2')
    eq_(rv.status_code, 200)


@test_context_admin
def test_details_ui_authorized(client):
    "Test that an admin can access the loan details ui"
    rv = client.get('/slaveloan/details/2')
    eq_(rv.status_code, 200)


@test_context
def test_machine_classes(client):
    "Test that someone not logged in can access the slave class mapping"
    rv = client.get('/machine/classes')
    eq_(rv.status_code, 200)
