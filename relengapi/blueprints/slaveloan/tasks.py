# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
import socket

from furl import furl

import bzrest
import requests

from requests import RequestException

from flask import current_app
from functools import wraps
from redo import retry
from relengapi.blueprints.slaveloan import bugzilla
from relengapi.blueprints.slaveloan import slave_mappings
from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines
from relengapi.lib.celery import task
from relengapi.util import tz

import celery
import logging

logger = logging.getLogger(__name__)


def add_task_to_history(loanid, msg):
    session = current_app.db.session('relengapi')
    l = session.query(Loans).get(loanid)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg=msg)
    session.add(history)
    session.commit()
    logger.debug("Log_line: %s" % msg)


def add_to_history(before=None, after=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            bound_task = None
            loanid = kwargs.get("loanid", None)
            if args and isinstance(args[0], celery.Task):
                bound_task = args[0]
            if before:
                add_task_to_history(loanid, before.format(**locals()))
            retval = f(*args, **kwargs)
            if after:
                add_task_to_history(loanid, after.format(**locals()))
            return retval
        return wrapper
    return decorator


@task(bind=True)
@add_to_history(
    before="Choosing an inhouse machine based on slavealloc",
    after="Chose inhouse machine {retval!s}")
def choose_inhouse_machine(self, loanid, loan_class):
    logger.debug("Choosing inhouse machine")
    url = furl(current_app.config.get("SLAVEALLOC_URL", None))
    # XXX: ToDo raise fatal if no slavealloc
    url.path.add("slaves")
    url.args["enabled"] = 1
    try:
        all_slaves = requests.get(str(url)).json()
    except RequestException as exc:
        logger.exception("Exception: %s" % exc)
        self.retry(exc=exc)
    # pylint silence
    # available_slaves = filter(slave_mappings.slave_filter(loan_class), all_slaves)
    available_slaves = [slave for slave in all_slaves
                        if slave_mappings.slave_filter(loan_class)(slave)]
    chosen = random.choice(available_slaves)
    logger.debug("Chosen Slave = %s" % chosen)
    return chosen['name']


@task(bind=True, max_retries=None)
@add_to_history(
    before="Identifying FQDN and IP of {args[1]}",
    after="Aquired FQDN and IP")
def fixup_machine(self, machine, loanid):
    try:
        fqdn = socket.getfqdn("%s.build.mozilla.org" % machine)
        ipaddr = socket.gethostbyname("%s.build.mozilla.org" % machine)
        session = current_app.db.session('relengapi')
        m = Machines.as_unique(session,
                               fqdn=fqdn,
                               ipaddr=ipaddr)
        l = session.query(Loans).get(loanid)
        l.machine = m
        session.commit()
        l = session.query(Loans).get(loanid)
    except Exception as exc:  # pylint: disable=W0703
        logger.exception(exc)
        self.retry(exc=exc)


@task(bind=True)
@add_to_history(
    before="Setup tracking bug for {args[1]}",
    after="Tracking bug {retval!s} linked with loan")
def bmo_set_tracking_bug(self, machine, loanid):
    try:
        session = current_app.db.session('relengapi')
        l = session.query(Loans).get(loanid)
        assert l.bug_id

        bug_comment = "Being loaned to %s in Bug %s" % (l.human.ldap, l.bug_id)

        tracking_bug = bugzilla.ProblemTrackingBug(machine, loadInfo=False)
        try:
            tracking_bug.refresh()
        except bzrest.errors.BugNotFound:
            logger.info("Couldn't find bug, creating it...")
            tracking_bug.create(comment=bug_comment, depends_on=l.bug_id)

        if tracking_bug.data:
            data = {
                "depends_on": {
                    "add": [l.bug_id],
                },
            }
            if not tracking_bug.data["is_open"]:
                data["status"] = "REOPENED"
            tracking_bug.add_comment(bug_comment, data=data)
        if not tracking_bug.id:
            raise ValueError("Unexpected result from bmo, retry")
        return tracking_bug.id
    except Exception as exc:
        logger.exception(exc)
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    before="Calling slaveapi's disable method",
    after="Disable request sent")
def start_disable_slave(self, machine, loanid):
    try:
        url = furl(current_app.config.get("SLAVEAPI_URL", None))
        # XXX: ToDo raise fatal if no slavealloc
        url.path.add(machine).add("actions").add("disable")
        postdata = dict(reason="Being loaned on slaveloan %s" % loanid)
        retry(requests.post, args=(str(url),), kwargs=dict(data=postdata)).json()
    except Exception as exc:  # pylint: disable=W0703
        logger.exception(exc)
        self.retry(exc=exc)


@task(bind=True)
@add_to_history(
    before="Filing the loan bug if needed",
    after="Loan is tracked in bug {retval!s}")
def bmo_file_loan_bug(self, loanid, slavetype, *args, **kwargs):
    try:
        session = current_app.db.session('relengapi')
        l = session.query(Loans).get(loanid)
        if l.bug_id:
            # Nothing to do, bug ID passed in
            return l.bug_id

        bmo_id = l.human.bugzilla
        bug_id = bugzilla.create_loan_bug(loan_id=loanid,
                                          slavetype=slavetype,
                                          bugzilla_username=bmo_id)
        if not bug_id:
            raise ValueError("Unexpected result from bmo, retry")
        l.bug_id = bug_id
        session.commit()
        return bug_id
    except Exception as exc:
        logger.exception(exc)
        self.retry(exc=exc)


@task()
def dummy_task(*args, **kwargs):
    pass

waitfor_disable_slave = dummy_task
slavealloc_disable = dummy_task
bmo_file_gpo_bug = dummy_task
bmo_wait_for_bug = dummy_task
bmo_file_tracking_bug = dummy_task
clean_secrets = dummy_task
update_loan_bug_with_details = dummy_task
email_loan_details = dummy_task
reboot_machine = dummy_task
register_action_needed = dummy_task
waitfor_action = dummy_task

# eof
