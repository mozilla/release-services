# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import flask_login
import sqlalchemy as sa
import structlog
from flask import Blueprint
from flask import g
from flask import render_template
from flask import url_for
from flask.ext.login import current_user
from sqlalchemy import asc
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import InternalServerError

from relengapi.blueprints.slaveloan import bugzilla
from relengapi.blueprints.slaveloan import rest
from relengapi.blueprints.slaveloan import task_groups
from relengapi.blueprints.slaveloan.model import History
from relengapi.blueprints.slaveloan.model import Humans
from relengapi.blueprints.slaveloan.model import Loans
from relengapi.blueprints.slaveloan.model import Machines
from relengapi.blueprints.slaveloan.model import ManualActions
from relengapi.blueprints.slaveloan.slave_mappings import slave_patterns
from relengapi.blueprints.slaveloan.slave_mappings import slave_to_slavetype
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib.api import apimethod
from relengapi.lib.permissions import p
from relengapi.util import tz

logger = structlog.get_logger()

bp = Blueprint('slaveloan', __name__,
               template_folder='templates',
               static_folder='static')

p.slaveloan.admin.doc("Administer Slaveloans for all users")

bp.root_widget_template('slaveloan_root_widget.html', priority=100)


@bp.record
def init_blueprint(state):
    bugzilla.init_app(state.app)

##################
#  RESTful APIs  #
##################


@bp.route('/loans/')
@p.slaveloan.admin.require()
@apimethod([rest.Loan], int)
def get_loans(all=None):
    """Get the list of loans you can see

    by default this only lists active (non complete) loans, use ``?all=1``
    if you want to list completed loans as well"""

    if all not in (None, 0, 1):
        raise BadRequest("Unexpected Value for 'all'.")

    # XXX: Use permissions to filter if not an admin
    loans = Loans.query
    if not all:
        loans = loans.filter(Loans.status != "COMPLETE")

    return [l.to_wsme() for l in loans.all()]


@bp.route('/loans/<int:loanid>')
@apimethod(rest.Loan, int)
def get_loan(loanid):
    "Get the details of a loan, by id"
    l = Loans.query.get(loanid)
    if not p.slaveloan.admin.can():
        if l.human.ldap != current_user.authenticated_email:
            raise Forbidden
    return l.to_wsme()


@bp.route('/loans/<int:loanid>', methods=["DELETE"])
@p.slaveloan.admin.require()
@apimethod(rest.Loan, int)
def complete_loan(loanid):
    "Get the details of a loan, by id"
    # XXX: Use permissions to ensure admin | loanee
    session = g.db.session('relengapi')
    l = session.query(Loans).get(loanid)
    l.status = "COMPLETE"
    hist_line = "%s marked loan as complete" % \
                (current_user.authenticated_email)
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg=hist_line)
    session.add(history)
    session.commit()
    return l.to_wsme()


@bp.route('/loans/<int:loanid>/history')
@p.slaveloan.admin.require()
@apimethod([rest.HistoryEntry], int)
def get_loan_history(loanid):
    "Get the history associated with this loan"
    # XXX: Use permissions to ensure admin | loanee
    histories = History.query \
                       .filter(History.loan_id == loanid) \
                       .order_by(asc(History.timestamp))
    return [h.to_wsme() for h in histories.all()]


@bp.route('/loans/', methods=['POST'])
@flask_login.login_required
@apimethod(rest.Loan, body=rest.LoanRequest)
def new_loan_request(body):
    "User Loan Requesting, returns the id of the loan"
    if not body.ldap_email:
        raise BadRequest("Missing LDAP E-Mail")
    if not p.slaveloan.admin.can():
        if not body.ldap_email == current_user.authenticated_email:
            raise BadRequest("You can't request loans on behalf of others.")
    if body.status:
        if not p.slaveloan.admin.can():
            raise Forbidden("Permission denied to set loan status manually")
        if body.status not in ["PENDING", "COMPLETE", "ACTIVE"]:
            raise BadRequest("Loan status (%s) is unsupported at this time" % body.status)

    if body.status and body.status != 'PENDING':
        if not body.fqdn:
            raise BadRequest("Must set Machine FQDN")
        if not body.ipaddress:
            raise BadRequest("Must set Machine IP Address")
    else:
        if body.fqdn or body.ipaddress:
            if p.slaveloan.admin.can():
                msg = ("Unable to explicitly set fqdn or ipaddress when not"
                       "also explicitly setting status")
                if body.status == "PENDING":
                    msg += " (to something other than PENDING)"
                raise BadRequest(msg)
            else:
                raise Forbidden("Permission denied to set fqdn and ipaddress manually")

    if not body.requested_slavetype:
        if not body.fqdn and not body.ipaddress:
            raise BadRequest("Missing slavetype")
    else:
        if body.fqdn or body.ipaddress:
            raise BadRequest("Unable to request a host if you're passing in the specifics")

        slavetype = slave_to_slavetype(body.requested_slavetype)
        if not slavetype:
            raise BadRequest("Unsupported slavetype")

    if not body.bugzilla_email:
        # Set bugzilla e-mail to ldap e-mail by default
        body.bugzilla_email = body.ldap_email

    session = g.db.session('relengapi')
    try:
        h = Humans.as_unique(session, ldap=body.ldap_email,
                             bugzilla=body.bugzilla_email)
        if h.bugzilla != body.bugzilla_email:
            h.bugzilla = body.bugzilla_email
    except sa.exc.IntegrityError:
        raise InternalServerError("Integrity Error from Database, please retry.")

    m = None
    if body.fqdn and body.ipaddress:
        try:
            m = Machines.as_unique(session, fqdn=body.fqdn,
                                   ipaddress=body.ipaddress)
        except sa.exc.IntegrityError:
            raise InternalServerError("Integrity Error from Database, please retry.")

    loan_data = dict(human=h)
    if body.loan_bug_id:
        loan_data.update(dict(bug_id=body.loan_bug_id))
    if m:
        loan_data.update(dict(machine=m))
    if body.status:
        loan_data.update(dict(status=body.status))
    else:
        loan_data.update(dict(status="PENDING"))

    l = Loans(**loan_data)

    if m:
        hist_line = "%s logged a %s loan on host: %s (ip: %s)" % \
                    (current_user.authenticated_email, body.status, body.fqdn,
                     body.ipaddress)
    else:
        hist_line = "%s issued a loan request for slavetype %s (original: '%s')" % \
                    (current_user.authenticated_email, slavetype,
                     body.requested_slavetype)
    if body.ldap_email != current_user.authenticated_email:
        hist_line += " on behalf of %s" % body.ldap_email
    history = History(for_loan=l,
                      timestamp=tz.utcnow(),
                      msg=hist_line)
    session.add(l)
    session.add(history)
    session.commit()
    logger.info(hist_line)
    if not m:
        chain_of_stuff = task_groups.generate_loan(loanid=l.id, slavetype=slavetype)
        chain_of_stuff.delay()
    return l.to_wsme()


@bp.route('/machine/classes')
@apimethod({unicode: [unicode]})
def get_machine_classes():
    """
    A mapping of what you'll get with a given loan, and globs of the slave types associated.

    Returns a mapping keyed on type of loan against slave-name globs that it corresponds to
    e.g.::

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


@bp.route('/manual_actions')
@flask_login.login_required
@p.slaveloan.admin.require()
@apimethod([rest.ManualAction], int, bool)
def get_loan_actions(loan_id=None, all=False):
    "Get the manual actions for a loan"
    action_query = ManualActions.query \
                                .order_by(asc(ManualActions.timestamp_start))
    if loan_id:
        action_query = action_query.filter(ManualActions.loan_id == loan_id)
    if not all:
        action_query = action_query.filter(ManualActions.timestamp_complete.is_(None))
    return [a.to_wsme() for a in action_query.all()]


@bp.route('/manual_actions/<int:action_id>')
@p.slaveloan.admin.require()
@apimethod(rest.ManualAction, int)
def get_loan_action(action_id):
    "Get a specific action for a loan"
    action = ManualActions.query.get(action_id)
    return action.to_wsme()


@bp.route('/manual_actions/<int:action_id>', methods=["PUT"])
@p.slaveloan.admin.require()
@apimethod(rest.ManualAction, int, body=rest.UpdateManualAction)
def update_loan_action(action_id, body):
    "Update a specific manual actions for a loan"
    session = g.db.session('relengapi')
    action = ManualActions.query.get(action_id)
    if body.complete and action.timestamp_complete is None:
        action.timestamp_complete = tz.utcnow()
        action.complete_by = current_user.authenticated_email
    elif not body.complete:
        raise BadRequest("Once actions are completed, cannot undo.")
    else:
        logger.debug("Attempted to complete this action twice")
        return action.to_wsme()
    session.add(action)
    history = History(loan_id=action.loan_id,
                      timestamp=tz.utcnow(),
                      msg="Admin marked action (id: %s) as complete via web" %
                          (action.id))
    session.add(history)
    session.commit()
    return action.to_wsme()


##################
# User Interface #
##################


@bp.route('/')
@flask_login.login_required
def root():
    return angular.template(
        'slaveloan_root.html',
        url_for('.static', filename='slaveloan_root.js'),
        machine_types=api.get_data(get_machine_classes),
        loan_request_url=url_for("slaveloan.new_loan_request"),
    )


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
