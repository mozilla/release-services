# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from nose.tools import assert_not_equal
from nose.tools import eq_
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
def test_bug_load_info(app):
    "Test that bug objects load their info properly"
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
def test_bug_refresh(app):
    "Test that bug objects refresh when asked"
    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.get_bug") as mockbzclient:
            mockbzclient.return_value = {'id': 12345, 'alias': "somealias"}
            bug = bugzilla.Bug(12345)
            eq_(bug.alias, "somealias")
            eq_(bug.id, 12345)
            eq_(bug.id_, 12345)
            olddata = bug.data
            # ID doesn't change...
            mockbzclient.return_value = {'id': 12345, 'alias': "newalias"}
            bug.refresh()
            eq_(bug.alias, "newalias")
            eq_(bug.id, 12345)
            assert_not_equal(olddata, bug.data)


@test_context
def test_bug_property_id_(app):
    "Test that bug id_ property exists and how it behaves"
    bug = bugzilla.Bug(12345, loadInfo=False)
    eq_(bug.id_, 12345)
    bug = bugzilla.Bug("somealias", loadInfo=False)
    eq_(bug.id_, "somealias")
    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.get_bug") as mockbzclient:
            mockbzclient.return_value = {'id': 12345, 'alias': "somealias"}
            bug = bugzilla.Bug("somealias")
            eq_(bug.id_, 12345)


@test_context
def test_problem_tracking_bug_slavename():
    "Test that slave_name is populated in problem tracking bug objects"
    # The slave name doesn't actually matter for this test
    slavename = "talos-mtnlion-r5-0010"
    bug = bugzilla.ProblemTrackingBug(slavename, loadInfo=False)
    eq_(bug.slave_name, slavename)
    eq_(bug.id_, slavename)
