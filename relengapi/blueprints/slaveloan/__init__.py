# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa
import logging
from flask import Blueprint
from flask import render_template
from flask import request
from flask import g
from relengapi import actions
from relengapi import db

from .model import Machines, Humans, Loans, History

logger = logging.getLogger(__name__)

bp = Blueprint('slaveloan', __name__,
               template_folder='templates')

_tbl_prefix = 'slaveloan_'


def get_current_loans(admin=True):
    session = g.db.session('relengapi')
    g.current_loaners = session.query(Loans)
    return

@bp.route('/loans/')
@apimethod()
def get_loans():
    loans = session.query(Loans)
    [l.to_json() for l in loans.all()]

@bp.route('/')
def root():
    return render_template('slaveloan_root.html')


@bp.route('/admin/')
def admin():
    get_current_loans(True)
    return render_template('slaveloan_admin.html')


@bp.route('/admin/', methods=['POST'])
def admin_post():
    import datetime
    logger.debug("Posting")
    form = request.form
    session = g.db.session('relengapi')
    m = Machines(fqdn=form.get('fqdn'), ipaddr=form.get('ipaddr'))
    h = Humans(ldap=form.get('LDAP'), bugzilla=form.get('bugzilla'))
    l = Loans(status=form.get('status'), human=h, machine=m)
    history = History(for_loan=l,
                      timestamp=datetime.datetime.utcnow(),
                      status=form.get('status'),
                      msg="adding to slave loan tool")
    session.add(l)
    session.add(h)
    session.commit()
    get_current_loans(True)
    return render_template('slaveloan_admin.html')
