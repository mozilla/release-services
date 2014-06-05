# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa
import logging
from flask import Blueprint
from flask import render_template
from flask import request
from flask import g
from werkzeug.exceptions import BadRequest
from relengapi import apimethod
from relengapi import db
from relengapi.util import tz
from .slave_mappings import slave_patterns

from .model import Machines, Humans, Loans, History

logger = logging.getLogger(__name__)

bp = Blueprint('slaveloan', __name__,
               template_folder='templates',
               static_folder='static')

_tbl_prefix = 'slaveloan_'


def get_current_loans(admin=True):
    session = g.db.session('relengapi')
    g.current_loaners = session.query(Loans)
    return


@bp.route('/machine/classes')
@apimethod()
def get_machine_classes():
    return slave_patterns()


@bp.route('/loans/')
@apimethod()
def get_loans():
    session = g.db.session('relengapi')
    loans = session.query(Loans).filter(Loans.machine != None)
    return [l.to_json() for l in loans.all()]


@bp.route('/')
def root():
    return render_template('slaveloan_root.html')


@bp.route('/admin/')
def admin():
    get_current_loans(True)
    return render_template('slaveloan_admin.html')


@bp.route('/admin/', methods=['POST'])
@apimethod()
def new_loan_from_admin():
    if 'status' not in request.json:
        raise BadRequest("Missing Status Field")
    if 'fqdn' not in request.json:
        raise BadRequest("Missing Machine FQDN")
    if 'ipaddr' not in request.json:
        raise BadRequest("Missing Machine IP Address")
    if 'LDAP' not in request.json:
        raise BadRequest("Missing LDAP E-Mail")
    if 'bugzilla' not in request.json:
        raise BadRequest("Missing Bugzilla E-Mail")

    session = g.db.session('relengapi')
    m = Machines.as_unique(session,
                           fqdn=request.json['fqdn'],
                           ipaddr=request.json['ipaddr'])
    h = Humans.as_unique(session,
                         ldap=request.json['LDAP'],
                         bugzilla=request.json['bugzilla'])
    l = Loans(status=request.json['status'],
              human=h,
              machine=m)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      status=request.json['status'],
                      msg="Adding to slave loan tool via admin interface")
    session.add(l)
    session.add(h)
    session.commit()
    return {'loan': l.to_json()}
