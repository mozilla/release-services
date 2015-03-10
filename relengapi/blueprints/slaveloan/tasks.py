# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
import socket

from furl import furl

import requests

from requests import RequestException

import datetime

from flask import current_app
from functools import wraps
from redo import retry
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
    logger.debug(repr(l.to_json()))
    logger.debug(repr(history.to_json()))
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
                logger.debug("Locals: %s" % repr(locals()))
                logger.debug("Log_line: %s" % before.format(**locals()))
                add_task_to_history(loanid, before.format(**locals()))
            retval = f(*args, **kwargs)
            if after:
                logger.debug("Locals: %s" % repr(locals()))
                logger.debug("AFTER: Log_line: %s" % after.format(**locals()))
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
        logger.debug("Exception")
        self.retry(exc=exc)
    logger.debug("Got all slaves")
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
        logger.debug("FIXUP MACHINE")
        fqdn = socket.getfqdn("%s.build.mozilla.org" % machine)
        logger.debug("FIXUP MACHINE = hostname: %s" % fqdn)
        ipaddr = socket.gethostbyname("%s.build.mozilla.org" % machine)
        logger.debug("FIXUP MACHINE = ipaddr: %s" % ipaddr)
        session = current_app.db.session('relengapi')
        m = Machines.as_unique(session,
                               fqdn=fqdn,
                               ipaddr=ipaddr)
        logger.debug("FIXUP MACHINE = machine.to_json(): %s" % m.to_json())
        l = session.query(Loans).get(loanid)
        logger.debug("FIXUP MACHINE = loan.to_json(): %s" % l.to_json())
        l.machine = m
        session.commit()
        l = session.query(Loans).get(loanid)
        logger.debug("FIXUP MACHINE = loan.to_json(): %s" % l.to_json())
    except Exception as exc:  # pylint: disable=W0703
        logger.debug("FIXUP MACHINE (FAILED)")
        logger.debug(exc)
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    before="Calling slaveapi's disable method",
    after="Disable request sent")
def start_disable_slave(self, machine, loanid):
    try:
        logger.debug("START DISABLE SLAVE")
        url = furl(current_app.config.get("SLAVEAPI_URL", None))
        # XXX: ToDo raise fatal if no slavealloc
        url.path.add(machine).add("actions").add("disable")
        logger.debug("START DISABLE SLAVE = url: %s" % str(url))
        postdata = dict(reason="Being loaned on slaveloan %s" % loanid)
        r = retry(requests.post, args=(str(url),), kwargs=dict(data=postdata)).json()
        logger.debug("START DISABLE SLAVE = r: %s" % str(r))
    except Exception as exc:  # pylint: disable=W0703
        self.retry(exc=exc)


@task()
def dummy_task(*args, **kwargs):
    pass

bmo_file_loan_bug = dummy_task
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
