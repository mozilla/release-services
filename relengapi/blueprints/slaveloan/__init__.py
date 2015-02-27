# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask_login
import logging
import sqlalchemy as sa
import wsme

from sqlalchemy import asc

from flask import Blueprint
from flask import g
from flask import render_template
from relengapi import apimethod
from relengapi import p
from relengapi.blueprints.slaveloan import task_groups
from relengapi.blueprints.slaveloan.slave_mappings import slave_patterns
from relengapi.util import tz
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import InternalServerError

from relengapi.blueprints.slaveloan import rest
from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Humans
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines

logger = logging.getLogger(__name__)

bp = Blueprint('slaveloan', __name__,
               template_folder='templates',
               static_folder='static')

p.slaveloan.admin.doc("Administer Slaveloans for all users")

##################
#  RESTful APIs  #
##################


@bp.route('/loans/')
@p.slaveloan.admin.require()
@apimethod([rest.Loan])
def get_loans():
    "Get the list of all `active` loans you can see"
    # XXX: Use permissions to filter if not an admin
    session = g.db.session('relengapi')
    loans = session.query(Loans).filter(Loans.machine_id.isnot(None))
    return [l.to_wsme() for l in loans.all()]


@bp.route('/loans/<int:loanid>')
@p.slaveloan.admin.require()
@apimethod(rest.Loan, int)
def get_loan(loanid):
    "Get the details of a loan, by id"
    # XXX: Use permissions to ensure admin | loanee
    session = g.db.session('relengapi')
    l = session.query(Loans).get(loanid)
    return l.to_wsme()


@bp.route('/loans/<int:loanid>/history')
@p.slaveloan.admin.require()
@apimethod([rest.HistoryEntry], int)
def get_loan_history(loanid):
    "Get the history associated with this loan"
    # XXX: Use permissions to ensure admin | loanee
    session = g.db.session('relengapi')
    histories = session.query(History) \
                       .filter(History.loan_id == loanid) \
                       .order_by(asc(History.timestamp))
    return [h.to_wsme() for h in histories.all()]


@bp.route('/loans/all')
@p.slaveloan.admin.require()
@apimethod([rest.Loan])
def get_all_loans():
    "Get the list of all loans you can see"
    # XXX: Use permissions to filter if not an admin
    session = g.db.session('relengapi')
    loans = session.query(Loans)
    return [l.to_wsme() for l in loans.all()]


@bp.route('/loans/new', methods=['POST'])
@p.slaveloan.admin.require()
@apimethod(None, body=rest.LoanRequest)
def new_loan_from_admin(body):
    "Creates a new loan entry"
    if not body.status:
        raise BadRequest("Missing Status Field")
    if not body.ldap_email:
        raise BadRequest("Missing LDAP E-Mail")
    if not body.bugzilla_email:
        raise BadRequest("Missing Bugzilla E-Mail")
    if body.status != 'PENDING':
        if not body.fqdn:
            raise BadRequest("Missing Machine FQDN")
        if not body.ipaddr:
            raise BadRequest("Missing Machine IP Address")

    session = g.db.session('relengapi')
    try:
        if body.status != 'PENDING':
            m = Machines.as_unique(session, fqdn=body.fqdn,
                                   ipaddr=body.ipaddr)
        h = Humans.as_unique(session, ldap=body.LDAP,
                             bugzilla=body.bugzilla)
    except sa.exc.IntegrityError:
        raise InternalServerError("Integrity Error from Database, please retry.")

    if body.status != 'PENDING':
        l = Loans(status=body.status, human=h, machine=m)
    else:
        l = Loans(status=body.status, human=h)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg="Adding to slave loan tool via admin interface")
    session.add(l)
    session.add(history)
    session.commit()
#    tasks.init_loan.delay(l.id, "bld-lion-r5")
    return None  # ?rest.WSME_New_Loan({'loan': l.to_wsme()})


@bp.route('/loans/request', methods=['POST'])
@apimethod(None, body=rest.LoanRequest)
def new_loan_request(body):
    "[ToDo] Implement User Loan Requesting"
    raise BadRequest("NotImplemented: User Requests are not implemented at this time")


@bp.route('/machine/classes')
@apimethod(
    wsme.types.DictType(
        key_type=unicode,
        value_type=wsme.types.ArrayType(unicode)
    )
)
def get_machine_classes():
    """
    A mapping of what you'll get with a given loan, and globs of the slave types associated.

    Returns a mapping keyed on type of loan against slave-name globs that it corresponds to
    e.g.:::

        {
            "b-2008-ix": [
                "b-2008-ix-*",
                "b-2008-sm-*",
                "w64-ix-*"
            ],
        }

    Where the above would tell you we are loaning a 'b-2008-ix' machine for slaves
    which match any of the globs in the array."""
    return slave_patterns()

##################
# User Interface #
##################


@bp.route('/')
@flask_login.login_required
def root():
    return render_template('slaveloan_root.html')


@bp.route('/details/<int:id>')
@flask_login.login_required
@p.slaveloan.admin.require()
def loan_details(id):
    g.loanid = id
    return render_template('slaveloan_details.html')


@bp.route('/admin/')
@flask_login.login_required
@p.slaveloan.admin.require()
def admin():
    return render_template('slaveloan_admin.html')

##################
# Temporary      #
##################


@bp.route('/tmp/')
@p.slaveloan.admin.require()
def init_loan():
    "Temporary, Manual testing only, DO NOT USE"
    chain_of_stuff = task_groups.generate_loan(loanid=18, slavetype="t-snow-r4")
    print "DEBUG", chain_of_stuff
    chain_of_stuff.delay()
    return render_template('slaveloan_admin.html')
