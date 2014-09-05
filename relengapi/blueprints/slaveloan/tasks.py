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


@task()
def init_loan(loanid, loan_class):
    print "Init Loan2", datetime.datetime.utcnow().isoformat(sep=" ")
    print "Loan Class = %s" % loan_class
    if slave_mappings.is_aws_serviceable(loan_class):
        print "aws host"
        # do_aws_loan.delay()
    else:
        print "physical host: %s" % loan_class
        choose_inhouse_machine.delay(loanid, loan_class)


@task(bind=True)
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


@task(bind=True, max_retries=None)
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
