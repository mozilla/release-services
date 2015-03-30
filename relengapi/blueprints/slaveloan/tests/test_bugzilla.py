# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import eq_
from nose.tools import ok_
from relengapi.blueprints.slaveloan import bugzilla
from relengapi.lib.testing.context import TestContext

test_context = TestContext()
test_context_servername = TestContext(config={'SERVER_NAME': "allizom.org"})


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


@test_context
def test_problem_tracking_bug_alias_length(app):
    "Test alias length on problem tracking bug creation"
    # The slave name doesn't actually matter for this test
    slavename = "talos-mtnlion-r5-0010"

    def create_bug_alias_ok(data):
        data['id'] = 12345
        eq_(data['alias'], slavename, msg="alias should be set when ok")
        return data

    def create_bug_alias_long(data):
        data['id'] = 12345
        eq_(data['alias'], None, msg="alias should be None when too long")
        return data

    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.create_bug") as mockcreatebug:
            with mock.patch("relengapi.blueprints.slaveloan.bugzilla.MAX_ALIAS", 50):
                mockcreatebug.side_effect = create_bug_alias_ok
                bug = bugzilla.ProblemTrackingBug(slavename, loadInfo=False)
                bug.create()
            with mock.patch("relengapi.blueprints.slaveloan.bugzilla.MAX_ALIAS", 5):
                mockcreatebug.side_effect = create_bug_alias_long
                bug = bugzilla.ProblemTrackingBug(slavename, loadInfo=False)
                bug.create()


@test_context
def test_problem_tracking_bug_create_comment(app):
    "Test problem tracking bug creation includes comment"
    # The slave name doesn't actually matter for this test
    slavename = "foobar"

    def create_bug_comment(data):
        data['id'] = 12345
        eq_(data['comment'], "some comment should be here")
        return data

    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.create_bug") as mockcreatebug:
            mockcreatebug.side_effect = create_bug_comment
            bug = bugzilla.ProblemTrackingBug(slavename, loadInfo=False)
            bug.create(comment="some comment should be here")


@test_context
def test_problem_tracking_bug_create_deps(app):
    "Test problem tracking bug creation includes depend"
    # The slave name doesn't actually matter for this test
    slavename = "foobar"

    def create_bug_comment(data):
        data['id'] = 12345
        eq_(data['depends_on'], 54321)
        return data

    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.create_bug") as mockcreatebug:
            mockcreatebug.side_effect = create_bug_comment
            bug = bugzilla.ProblemTrackingBug(slavename, loadInfo=False)
            bug.create(depends_on=54321)


@test_context
def test_create_loan_bug_valueerror(app):
    "Test that varying missing input combinations to create_loan_bug raises an exception"
    clb = bugzilla.create_loan_bug
    with app.app_context():
        assert_raises(ValueError, clb)
        assert_raises(ValueError, clb, loan_id=12345)
        assert_raises(ValueError, clb, slavetype="foobar")
        assert_raises(ValueError, clb, bugzilla_username="me@example.com")
        assert_raises(ValueError, clb, loan_id=12345, slavetype="foobar")
        assert_raises(ValueError, clb, loan_id=12345, bugzilla_username="me@example.com")
        assert_raises(ValueError, clb, slavetype="foobar", bugzilla_username="me@example.com")


@test_context
def test_create_loan_bug_servername(app):
    "Test problem loan bug creation requires SERVER_NAME set"
    # The slave name doesn't actually matter for this test
    slavetype = "foobar"
    who = "me@example.com"
    loan_id = 10

    with app.app_context():
        assert_raises(
            RuntimeError, bugzilla.create_loan_bug,
            loan_id=loan_id, slavetype=slavetype, bugzilla_username=who)


@test_context_servername
def test_create_loan_bug(app):
    "Test problem loan bug creation includes stuff"
    # The slave name doesn't actually matter for this test
    slavetype = "foobar"
    who = "me@example.com"
    loan_id = 123456789

    def create_bug_comment(data):
        data['id'] = 12345
        ok_("summary" in data, msg="creation includes bug summary")
        ok_(slavetype in data['summary'], msg="bug summary includes slavetype")
        ok_(who in data['summary'], msg="bug summary includes who")
        ok_("comment" in data, msg="creation includes initial comment")
        ok_(slavetype in data['comment'], msg="comment includes slavetype")
        ok_(who in data['comment'], msg="comment includes who")
        ok_(str(loan_id) in data['comment'], msg="the loan id must appear in the comment")
        return data

    with app.app_context():
        with mock.patch("bzrest.client.BugzillaClient.create_bug") as mockcreatebug:
            mockcreatebug.side_effect = create_bug_comment
            bugzilla.create_loan_bug(loan_id=loan_id, slavetype=slavetype, bugzilla_username=who)
