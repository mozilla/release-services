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
from relengapi.blueprints.slaveloan.model import ManualActions
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


@task(bind=True)
@add_to_history(
    before="Identifying aws machine name to use",
    after="Chose aws machine {retval!s}")
def choose_aws_machine(self, loanid, loan_class):
    logger.debug("Choosing aws machine name")
    # We use foo-$user_shortname$N where $N is optional only if
    # there exists another active loan with the foo-$user prefix
    l = Loans.query.get(loanid)
    prefix = slave_mappings.slavetype_to_awsprefix(loan_class)
    user_shortname = l.human.ldap.split("@")[0]
    bare_name = prefix + "-" + user_shortname
    similar_loans = Loans.query \
                         .filter(Loans.machine_id == Machines.id) \
                         .filter(Machines.fqdn.like(bare_name + "%")) \
                         .filter(~Loans.status.in_(["COMPLETE"])) \
                         .order_by(Machines.fqdn.desc())
    if similar_loans.count():
        existing_aws_loan = similar_loans.first().machine.fqdn
        shortname = existing_aws_loan.split(".")[0]
        this_name = bare_name + str(int(shortname[len(bare_name):])) + 1
    else:
        this_name = bare_name
    logger.debug("Chosen Slave Name = %s" % this_name)
    return this_name


@task(bind=True, max_retries=None)
@add_to_history(
    before="Identifying FQDN and IP of {args[1]}",
    after="Acquired FQDN and IP")
def fixup_machine(self, machine, loanid):
    try:
        fqdn = socket.getfqdn("%s.build.mozilla.org" % machine)
        ipaddress = socket.gethostbyname("%s.build.mozilla.org" % machine)
        session = current_app.db.session('relengapi')
        m = Machines.as_unique(session,
                               fqdn=fqdn,
                               ipaddress=ipaddress)
        #  Re-check validity of fqdn and ip
        if m.fqdn != fqdn:
            m.fqdn = fqdn
        if m.ipaddress != ipaddress:
            m.ipaddress = ipaddress
        l = session.query(Loans).get(loanid)
        l.machine = m
        session.commit()
    except Exception as exc:  # pylint: disable=W0703
        logger.exception(exc)
        self.retry(exc=exc)


@task(bind=True)
@add_to_history(
    before="Setup tracking bug for {args[1]}",
    after="Tracking bug {retval!s} linked with loan")
def bmo_set_tracking_bug(self, machine, loanid):
    try:
        l = Loans.query.get(loanid)
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
    before="Disabling in slavealloc (via slaveapi)",
    after="Disable request sent to slavealloc (via slaveapi)")
def slavealloc_disable(self, machine, loanid):
    try:
        url = furl(current_app.config.get("SLAVEAPI_URL", None))
        url.path.add(machine).add("actions").add("disable")
        loan_bug = Loans.query.get(loanid).bug_id
        postdata = dict(reason="Being loaned on slaveloan bug %s" % loan_bug)
        retry(requests.post, args=(str(url),), kwargs=dict(data=postdata)).json()
        return machine
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


@task(bind=True)
@add_to_history(
    after="Waiting for a human to perform {kwargs[action_name]} (id {retval!s})")
def register_action_needed(self, loanid, action_name):
    if not action_name:
        raise ValueError("must supply an action name")
    try:
        session = current_app.db.session('relengapi')
        l = session.query(Loans).get(loanid)
        if action_name == "add_to_vpn":
            action_message = (
                "Add user (%s) and machine (%s) to the VPN. "
                "Following https://wiki.mozilla.org/ReleaseEngineering/How_To/Update_VPN_ACL"
                % (l.human.ldap, l.machine.fqdn)
            )
        elif action_name == "create_aws_system":
            action_message = (
                "Create an aws machine for %s of the type requested (see loan history)."
                " Following "
                "https://wiki.mozilla.org/ReleaseEngineering/How_To/Loan_a_Slave#AWS_machines"
                % (l.human.ldap,)
            )
        elif action_name == "clean_secrets":
            action_message = (
                "Clean secrets from the machine. See instructions at "
                "https://wiki.mozilla.org/ReleaseEngineering/How_To/Loan_a_Slave#Cleaning"
            )
        elif action_name == "notify_complete":
            action_message = (
                "Notify the loanee in e-mail and the loan bug (Bug %s) that the loan is ready. "
                "See template text for both in "
                "https://wiki.mozilla.org/ReleaseEngineering/How_To/Loan_a_Slave#Notifying"
                % l.bug_id
            )
        elif action_name == "gpo_switch":
            action_message = (
                "Need to switch host (%s) to be in the Loaner GPO group. Follow "
                "https://wiki.mozilla.org/ReleaseEngineering/How_To/Loan_a_Slave"
                "#t-xp32-ix.2C_t-w732-ix.2C_t-w864-ix.2C_w64-ix-slave "
                "for more information"
                % (l.machine.fqdn)
            )
        else:
            raise ValueError("Invalid action name")
        action = ManualActions(for_loan=l,
                               timestamp_start=tz.utcnow(),
                               msg=action_message)
        session.add(action)
        session.commit()
        return action.id
    except ValueError:
        raise  # Don't indefinitely retry in this case
    except Exception as exc:
        self.retry(exc=exc)


@task(bind=True, max_retries=None, default_retry_delay=60)
@add_to_history(
    after="Noticed that a human performed pending action (id {args[1]}), continuing")
def waitfor_action(self, action_id, loanid):
    try:
        action = ManualActions.query.get(action_id)
        if not action.timestamp_complete:
            raise Exception("Retry me")
    except Exception as exc:
        logger.debug("Retrying...")
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    before="Calling slaveapi's disable method to disable from buildbot",
    after="Disable request sent")
def start_disable_slave(self, machine, loanid):
    try:
        url = furl(current_app.config.get("SLAVEAPI_URL", None))
        url.path.add(machine).add("actions").add("shutdown_buildslave")
        ret = retry(requests.post, args=(str(url),), ).json()
        return (ret["requestid"], machine)
    except Exception as exc:
        logger.exception(exc)
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    after="Noticed that machine was disabled (or waiting timed out)")
def waitfor_disable_slave(self, data, loanid):
    requestid, machine = data
    try:
        url = furl(current_app.config.get("SLAVEAPI_URL", None))
        url.path.add(machine).add("actions").add("shutdown_buildslave")
        url.args["requestid"] = requestid
        ret = retry(requests.get, args=(str(url),), kwargs=dict()).json()
        if ret["state"] in (0, 1):
            # 0 = PENDING, 1 = RUNNING (3=Failed and 2=Success)
            raise Exception("Continue waiting for disabled slave")
    except Exception as exc:
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    after="Marked loan as ACTIVE")
def mark_loan_status(self, loanid, status):
    try:
        session = current_app.db.session('relengapi')
        l = session.query(Loans).get(loanid)
        l.status = status
        session.commit()
    except Exception as exc:
        self.retry(exc=exc)


@task()
def dummy_task(*args, **kwargs):
    pass

bmo_file_gpo_bug = dummy_task
bmo_waitfor_bug = dummy_task
clean_secrets = dummy_task
update_loan_bug_with_details = dummy_task
email_loan_details = dummy_task
