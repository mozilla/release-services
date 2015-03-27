# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
import mock
from relengapi.blueprints.slaveloan import bugzilla
from relengapi.lib.testing.context import TestContext

test_context = TestContext()


@test_context
def test_base_bug_object(client):
    "Test how the bug object stores alias or id"
    bug = bugzilla.Bug(12345, loadInfo=False)
    eq_(bug.id, 12345)
    eq_(bug.alias, None)
    bug = bugzilla.Bug("somealias", loadInfo=False)
    eq_(bug.id, None)
    eq_(bug.alias, "somealias")


@test_context
def test_base_bug_empty_object(client):
    "Test that a bug object can be created without passing either alias or id"
    bug = bugzilla.Bug()
    eq_(bug.id, None)
    eq_(bug.alias, None)


@test_context
def test_bug_refresh(app):
    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.get_bug") as mockbzclient:
            mockbzclient.return_value = {'id': 12345, 'alias': "somealias"}
            bug = bugzilla.Bug(12345)
            eq_(bug.alias, "somealias")
            eq_(bug.id, 12345)
            eq_(bug.id_, 12345)
            bug = bugzilla.Bug("somealias")
            eq_(bug.alias, "somealias")
            eq_(bug.id, 12345)


@test_context
def test_bug_property_id_(client):
    "Test that bug id_ exists and how it behaves"
    bug = bugzilla.Bug(12345, loadInfo=False)
    eq_(bug.id_, 12345)
    bug = bugzilla.Bug("somealias", loadInfo=False)
    eq_(bug.id_, "somealias")
    with mock.patch("bzrest.client.BugzillaClient.get_bug") as mockbzclient:
        mockbzclient.return_value = {'id': 12345, 'alias': "somealias"}
        bug = bugzilla.Bug("somealias", loadInfo=False)
        eq_(bug.id_, 12345)
