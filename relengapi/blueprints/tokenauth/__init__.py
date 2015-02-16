# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from flask import Blueprint
from flask import g
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_required
from relengapi import apimethod
from relengapi import p
from relengapi.blueprints.tokenauth import loader
from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth import tokenstr
from relengapi.blueprints.tokenauth import types
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import auth
from relengapi.lib import permissions
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

logger = logging.getLogger(__name__)
bp = Blueprint('tokenauth', __name__,
               template_folder='templates',
               static_folder='static')

p.base.tokens.view.doc('See authentication token metadata')
p.base.tokens.issue.doc('Issue new authentication tokens')
p.base.tokens.revoke.doc('Revoke authentication tokens')


def permitted():
    return permissions.can(p.base.tokens.view,
                           p.base.tokens.issue,
                           p.base.tokens.revoke)
bp.root_widget_template(
    'tokenauth_root_widget.html', priority=100, condition=permitted)


@bp.route('/')
@login_required
def root():
    return angular.template('tokens.html',
                            url_for('.static', filename='tokens.js'),
                            tokens=api.get_data(list_tokens))


@bp.route('/tokens')
@p.base.tokens.view.require()
@apimethod([types.JsonToken])
def list_tokens():
    """Get a list of all existing tokens.

    Note that the response does not include the actual token strings.
    Such strings are only revealed when creating a new token."""
    return [t.to_jsontoken() for t in tables.Token.query.all()]


@bp.route('/tokens', methods=['POST'])
@apimethod(types.JsonToken, body=types.JsonToken)
@p.base.tokens.issue.require()
def issue_token(body):
    """Issue a new token.  The body should not include a ``token`` or ``id``.
    The response will contain both."""
    requested_permissions = [p.get(a) for a in body.permissions]
    # ensure the request is for a subset of the permissions the user can
    # perform
    if None in requested_permissions or not set(requested_permissions) <= current_user.permissions:
        raise BadRequest("bad permissions")

    session = g.db.session('relengapi')
    token_row = tables.Token(
        description=body.description,
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    rv = token_row.to_jsontoken()
    rv.token = tokenstr.claims_to_str(
        {'id': token_row.id})
    return rv


@bp.route('/tokens/<int:token_id>')
@apimethod(types.JsonToken, int)
@p.base.tokens.view.require()
def get_token(token_id):
    """Get a token, identified by its ``id``."""
    token_data = tables.Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound
    return token_data.to_jsontoken()


@bp.route('/tokens/query', methods=['POST'])
@p.base.tokens.view.require()
@apimethod(types.JsonToken, body=unicode)
def get_token_by_token(body):
    """Get a token, specified by the token key given in the request body
    (this avoids embedding a token in a URL, where it might be logged)."""
    token_str = body
    claims = tokenstr.str_to_claims(token_str)
    if not claims:
        raise NotFound

    token_data = tables.Token.query.filter_by(id=claims['id']).first()
    if not token_data:
        raise NotFound
    return token_data.to_jsontoken()


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@apimethod(None, int)
@p.base.tokens.revoke.require()
def revoke_token(token_id):
    """Revoke an authentication token, identified by its ID."""
    session = g.db.session('relengapi')
    tables.Token.query.filter_by(id=token_id).delete()
    session.commit()
    return None, 204


# enable the loader to get a look at each incoming request
auth.request_loader(loader.token_loader)


@bp.record
def init_blueprint(state):
    tokenstr.init_app(state.app)
