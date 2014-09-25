# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
import socket
from furl import furl

import requests
from requests import RequestException

from flask import current_app
from relengapi.lib.celery import task
from relengapi.blueprints.slaveloan import slave_mappings
from relengapi.blueprints.slaveloan.model import Machines, Humans, Loans, History
from redo import retry
import datetime
from functools import wraps
from relengapi.util import tz

import celery


def add_task_to_history(loanid, msg):
    session = current_app.db.session('relengapi')
    l = session.query(Loans).get(loanid)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg=msg)
    session.add(history)
    session.commit()
    print "DEBUG:", repr(l.to_json())
    print "DEBUG:", repr(history.to_json())
    print "DEBUG: Log_line: %s" % msg


def add_to_history(before=None, after=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            bound_task = None
            loanid = None
            if isinstance(args[0], celery.Task):
                bound_task = args[0]
                loanid = args[1]
            else:
                loanid = args[0]
            if before:
                print "DEBUG: Locals: %s" % repr(locals())
                print "DEBUG: Log_line: %s" % before.format(**locals())
                add_task_to_history(loanid, before.format(**locals()))
            retval = f(*args, **kwargs)
            if after:
                print "DEBUG: Locals: %s" % repr(locals())
                print "DEBUG: AFTER: Log_line: %s" % after.format(**locals())
                add_task_to_history(loanid, after.format(**locals()))
            return retval
        return wrapper
    return decorator


@task()
@add_to_history(
    before="Initialising Loan for slaveclass {args[1]!s}",
    after="Initialising Loan Process Complete for slaveclass {args[1]!s}, using flow {retval!s}")
def init_loan(loanid, loan_class):
    print "Init Loan2", datetime.datetime.utcnow().isoformat(sep=" ")
    print "Loan Class = %s" % loan_class
    if slave_mappings.is_aws_serviceable(loan_class):
        print "aws host"
        # do_aws_loan.delay()
        return "AWS"
    else:
        print "physical host: %s" % loan_class
        choose_inhouse_machine.delay(loanid, loan_class)
        return "inhouse"


@task(bind=True)
@add_to_history(
    before="Choosing an inhouse machine based on slavealloc",
    after="Chose inhouse machine {retval!s}")
def choose_inhouse_machine(self, loanid, loan_class):
    print "Choosing inhouse machine"
    url = furl("http://slavealloc.pvt.build.mozilla.org/api/slaves")
    url.args["enabled"] = 1
    try:
        all_slaves = requests.get(str(url)).json()
    except RequestException as exc:
        print "Exception"
        self.retry(exc=exc)
    print "Got all slaves"
    # pylint silence
    # available_slaves = filter(slave_mappings.slave_filter(loan_class), all_slaves)
    available_slaves = [slave for slave in all_slaves
                        if slave_mappings.slave_filter(loan_class)(slave)]
    chosen = random.choice(available_slaves)
    print "Chosen Slave = %s" % chosen
    fixup_machine.delay(loanid, chosen['name'])
    start_disable_slave.delay(loanid, chosen['name'])
    return chosen['name']


@task(bind=True, max_retries=None)
@add_to_history(
    before="Identifying FQDN and IP of {args[2]}",
    after="Aquired FQDN and IP")
def fixup_machine(self, loanid, machine):
    try:
        print "FIXUP MACHINE"
        fqdn = socket.getfqdn("%s.build.mozilla.org" % machine)
        print "FIXUP MACHINE = hostname: %s" % fqdn
        ipaddr = socket.gethostbyname("%s.build.mozilla.org" % machine)
        print "FIXUP MACHINE = ipaddr: %s" % ipaddr
        session = current_app.db.session('relengapi')
        m = Machines.as_unique(session,
                               fqdn=fqdn,
                               ipaddr=ipaddr)
        print "FIXUP MACHINE = machine.to_json(): %s" % m.to_json()
        l = session.query(Loans).get(loanid)
        print "FIXUP MACHINE = loan.to_json(): %s" % l.to_json()
        l.machine = m
        session.commit()
        l = session.query(Loans).get(loanid)
        print "FIXUP MACHINE = loan.to_json(): %s" % l.to_json()
    except Exception as exc:  # pylint: disable=W0703
        print "FIXUP MACHINE (FAILED)"
        print exc
        self.retry(exc=exc)


@task(bind=True, max_retries=None)
@add_to_history(
    before="Calling slaveapi's disable method",
    after="Disable request sent")
def start_disable_slave(self, loanid, machine):
    try:
        print "START DISABLE SLAVE"
        slaveapi = "http://slaveapi-dev1.build.mozilla.org:8080/slaves/"
        url = furl(slaveapi)
        url.path.add(machine).add("actions").add("disable")
        print "START DISABLE SLAVE = url: %s" % str(url)
        postdata = dict(reason="Being loaned on slaveloan %s" % loanid)
        r = retry(requests.post, args=(str(url),), kwargs=dict(data=postdata)).json()
        print "START DISABLE SLAVE = r: %s" % str(r)
        raise
    except Exception as exc:  # pylint: disable=W0703
        self.retry(exc=exc)

if __name__ == "__main__":
    temporary_silence_pylint = History
    temporary_silence_pylint = Humans
