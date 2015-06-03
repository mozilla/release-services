# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# XXX Much of this functionality should probably be its own
#     Separate relengapi blueprint

import logging

from bzrest.client import BugzillaClient
from flask import current_app
from flask import url_for

log = logging.getLogger(__name__)

MAX_ALIAS = 15
DEFAULT_BUGZILLA_URL = "https://bugzilla-dev.allizom.org/rest/"


def init_app(app):
    bzurl = app.config.get('BUGZILLA_URL', DEFAULT_BUGZILLA_URL)
    if not app.config.get('BUGZILLA_USER', None):
        log.warning("No bugzilla user specified. (Set BUGZILLA_USER in config to fix)")
    if not app.config.get('BUGZILLA_PASS', None):
        log.warning("No bugzilla password specified. (Set BUGZILLA_PASS in config to fix)")
    bzclient = BugzillaClient()
    bzclient.configure(bzurl=bzurl,
                       username=app.config.get('BUGZILLA_USER', None),
                       password=app.config.get('BUGZILLA_PASS', None))
    app.bzclient = bzclient


class Bug(object):
    alias = None
    id = None

    def __init__(self, id_=None, loadInfo=True):
        if isinstance(id_, int):
            self.id = id_
        else:
            self.alias = id_
        self.data = {}
        if id_ and loadInfo:
            self.refresh()

    @property
    def id_(self):
        return self.id or self.alias

    def refresh(self):
        self.data = current_app.bzclient.get_bug(self.id_)
        self.id = self.data["id"]
        self.alias = self.data["alias"]

    def add_comment(self, comment, data={}):
        return current_app.bzclient.add_comment(self.id_, comment, data)


class ProblemTrackingBug(Bug):
    product = "Release Engineering"
    component = "Buildduty"

    def __init__(self, slave_name, *args, **kwargs):
        self.slave_name = slave_name
        Bug.__init__(self, id_=slave_name, *args, **kwargs)

    def create(self, comment=None, depends_on=None):
        if len(self.slave_name) > MAX_ALIAS:
            alias = None
        else:
            alias = self.slave_name
        data = {
            "product": self.product,
            "component": self.component,
            "summary": "%s problem tracking" % self.slave_name,
            "version": "other",
            "alias": alias,
            # todo: do we care about setting these correctly?
            "op_sys": "All",
            "platform": "All"
        }
        if comment:
            data['comment'] = comment
        if depends_on:
            data['depends_on'] = depends_on
        resp = current_app.bzclient.create_bug(data)
        self.id = resp["id"]


class LoanerBug(Bug):
    product = "Release Engineering"
    component = "Loan Requests"

    def __init__(self, *args, **kwargs):
        Bug.__init__(self, *args, **kwargs)

    def create(self, summary=None, comment=None, blocks=None):
        data = {
            "product": self.product,
            "component": self.component,
            "summary": summary,
            "version": "other",
            # todo: do we care about setting these correctly?
            "op_sys": "All",
            "platform": "All"
        }
        if comment:
            data['comment'] = comment
        if blocks:
            data['blocks'] = blocks
        resp = current_app.bzclient.create_bug(data)
        self.id = resp["id"]
        return self


LOAN_SUMMARY = u"Loan a slave of {slavetype} to {human}"
COMMENT_ZERO = u"""{human} is in need of a slaveloan from slavetype {slavetype}

(this bug was auto-created from the slaveloan tool)
{loan_url}"""


def create_loan_bug(loan_id=None, slavetype=None, bugzilla_username=None):
    if None in (loan_id, slavetype, bugzilla_username):
        raise ValueError("Missing arguments")

    summary = LOAN_SUMMARY.format(slavetype=slavetype,
                                  human=bugzilla_username)
    c_zero = COMMENT_ZERO.format(
        slavetype=slavetype,
        human=bugzilla_username,
        loan_url=url_for("slaveloan.loan_details", id=loan_id))
    loan_bug = LoanerBug(loadInfo=False)
    bug = loan_bug.create(comment=c_zero, summary=summary)
    return bug.id
