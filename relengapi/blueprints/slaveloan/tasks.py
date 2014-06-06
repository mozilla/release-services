# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import random
from furl import furl

import requests
from requests import RequestException

from relengapi.celery import task
from relengapi.blueprints.slaveloan import slave_mappings
import datetime


@task()
def init_loan(loan_class):
    print "Init Loan2", datetime.datetime.utcnow().isoformat(sep=" ")
    print "Loan Class = %s" % loan_class
    if slave_mappings.is_aws_serviceable(loan_class):
        print "aws host"
        pass  # do_aws_loan.delay()
    else:
        print "physical host"
        choose_inhouse_machine.delay(loan_class)


@task(bind=True, max_retries=None)
def choose_inhouse_machine(self, loan_class):
    print "Choosing inhouse machine"
    url = furl("http://slavealloc.pvt.build.mozilla.org/api/slaves")
    url.args["enabled"] = 1
    try:
        all_slaves = requests.get(str(url)).json()
    except RequestException as exc:
        print "Exception"
        self.retry(exc=exc)
    print "Got all slaves"
    available_slaves = filter(slave_mappings.filter_slaves(loan_class), all_slaves)
    chosen = random.choice(available_slaves)
    print "Chosen Slave = %s" % chosen
