# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask_login
import logging
import sqlalchemy as sa
import wsme.types

from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from relengapi import apimethod
from relengapi import p
from relengapi.blueprints.slaveloan import tasks
from relengapi.blueprints.slaveloan.slave_mappings import slave_patterns
from relengapi.util import tz
from werkzeug.exceptions import BadRequest

from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Humans
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines
from relengapi.blueprints.slaveloan.model import WSME_Loan_Loans_Table
from relengapi.blueprints.slaveloan.model import WSME_Loan_Loans_Table

logger = logging.getLogger(__name__)

bp = Blueprint('slaveloan', __name__,
               template_folder='templates',
               static_folder='static')

_tbl_prefix = 'slaveloan_'
p.slaveloan.admin.doc("Administer Slaveloans for all users")


WSME_Machine_Class = wsme.types.DictType(key_type=unicode,
                                         value_type=wsme.types.ArrayType(unicode))


class WSME_New_Loan(wsme.types.Base):
    """The loan object that was created"""
    loan = WSME_Loan_Loans_Table


@bp.route('/machine/classes')
@apimethod(WSME_Machine_Class)
def get_machine_classes():
    return slave_patterns()


@bp.route('/loans/')
@apimethod([WSME_Loan_Loans_Table])
def get_loans():
    session = g.db.session('relengapi')
    loans = session.query(Loans).filter(Loans.machine_id.isnot(None))
    return [l.to_wsme() for l in loans.all()]


@bp.route('/loans/all')
@apimethod([WSME_Loan_Loans_Table])
def get_all_loans():
    session = g.db.session('relengapi')
    loans = session.query(Loans)
    return [l.to_wsme() for l in loans.all()]


@bp.route('/')
@flask_login.login_required
def root():
    return render_template('slaveloan_root.html')


@bp.route('/admin/')
@flask_login.login_required
@p.slaveloan.admin.require()
def admin():
    return render_template('slaveloan_admin.html')


@bp.route('/admin/', methods=['POST'])
@p.slaveloan.admin.require()
@apimethod(WSME_New_Loan)
def new_loan_from_admin():
    if 'status' not in request.json:
        raise BadRequest("Missing Status Field")
    if 'LDAP' not in request.json:
        raise BadRequest("Missing LDAP E-Mail")
    if 'bugzilla' not in request.json:
        raise BadRequest("Missing Bugzilla E-Mail")
    if request.json['status'] != 'PENDING':
        if 'fqdn' not in request.json:
            raise BadRequest("Missing Machine FQDN")
        if 'ipaddr' not in request.json:
            raise BadRequest("Missing Machine IP Address")

    session = g.db.session('relengapi')
    try:
        if request.json['status'] != 'PENDING':
            m = Machines.as_unique(session,
                                   fqdn=request.json['fqdn'],
                                   ipaddr=request.json['ipaddr'])
        h = Humans.as_unique(session,
                             ldap=request.json['LDAP'],
                             bugzilla=request.json['bugzilla'])
    except sa.exc.IntegrityError:
        raise BadRequest("Integrity Error from Database, please retry.")

    if request.json['status'] != 'PENDING':
        l = Loans(status=request.json['status'],
                  human=h,
                  machine=m)
    else:
        l = Loans(status=request.json['status'],
                  human=h)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg="Adding to slave loan tool via admin interface")
    session.add(l)
    session.add(history)
    session.commit()
#    tasks.init_loan.delay(l.id, "bld-lion-r5")
    return WSME_New_Loan({'loan': l.to_wsme()})


@bp.route('/tmp/')
def init_loan():
    tasks.init_loan.delay(18, "t-snow-r4")
    return render_template('slaveloan_admin.html')
