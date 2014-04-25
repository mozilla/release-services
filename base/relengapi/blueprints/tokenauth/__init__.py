# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi import db
import logging
import sqlalchemy as sa
from flask import g
from flask import Blueprint
from flask import current_app
from flask import render_template
from flask import request
from flask.ext.principal import Identity
from flask.ext.login import login_required
from relengapi import actions
from relengapi import principal
from relengapi import apimethod
from itsdangerous import JSONWebSignatureSerializer, BadData
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

TOKENAUTH_VERSION = 1
logger = logging.getLogger(__name__)
bp = Blueprint('tokenauth', __name__,
               template_folder='templates',
               static_folder='static')

actions.base.tokens.view.doc('See authentication token metadata')
actions.base.tokens.issue.doc('Issue new authentication tokens')
actions.base.tokens.revoke.doc('Revoke authentication tokens')


class Token(db.declarative_base('relengapi')):
    __tablename__ = 'auth_tokens'

    def __init__(self, actions=[], **kwargs):
        kwargs['_actions'] = ','.join(map(str, actions))
        super(Token, self).__init__(**kwargs)

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)
    _actions = sa.Column(sa.Text, nullable=False)

    def to_json(self):
        return dict(id=self.id, description=self.description, actions=map(str, self.actions))

    @property
    def actions(self):
        token_actions = [actions.get(actionstr)
                         for actionstr in self._actions.split(',')]
        # silently ignore any nonexistent actions; this allows us to remove unused
        # actions without causing tokens permitting those actions to fail
        # completely
        return filter(None, token_actions)


@bp.route('/')
@login_required
def root():
    available_actions = sorted((str(a), a.__doc__)
                               for a in g.identity.provides)
    return render_template('new-token.html',
                           available_actions=available_actions)


@bp.route('/tokens')
@apimethod()
@actions.base.tokens.view.require()
def list_tokens():
    """Get the list of all tokens.  Note that the response does not include the
    actual token strings."""
    return [t.to_json() for t in Token.query.all()]


@bp.route('/tokens', methods=['POST'])
@apimethod()
@actions.base.tokens.issue.require()
def issue_token():
    """Issue a new authentication token.  The POST body must contain JSON with keys
    'actions', a list of allowed actions; and description, a description of the token."""
    requested_actions = map(actions.get, request.json['actions'])
    # ensure the request is for a subset of the actions the user can perform
    if None in requested_actions or not set(requested_actions) <= g.identity.provides:
        raise BadRequest("bad actions")
    if 'description' not in request.json:
        raise BadRequest("no description")

    session = g.db.session('relengapi')
    token_row = Token(
        description=request.json['description'],
        actions=requested_actions)
    session.add(token_row)
    session.commit()

    token = current_app.tokenauth_serializer.dumps(
        {'v': TOKENAUTH_VERSION, 'id': token_row.id})
    return {'token': token}


@bp.route('/tokens/<int:token_id>')
@apimethod()
@actions.base.tokens.view.require()
def get_token(token_id):
    """Get a token, identified by its ID."""
    token_data = Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound
    return token_data.to_json()


@bp.route('/tokens/query', methods=['POST'])
@apimethod()
@actions.base.tokens.view.require()
def get_token_by_token():
    """Get a token, specified by the 'token' key in the request body.
    This is done to avoid embedding a token in a URL, where it might be
    logged."""
    if 'token' not in request.json:
        raise NotFound
    token_str = request.json['token']
    try:
        token_info = current_app.tokenauth_serializer.loads(token_str)
    except BadData:
        raise NotFound
    if token_info['v'] != TOKENAUTH_VERSION:
        raise NotFound
    token_data = Token.query.filter_by(id=token_info['id']).first()
    if not token_data:
        raise NotFound
    return token_data.to_json()


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@apimethod()
@actions.base.tokens.revoke.require()
def revoke_token(token_id):
    """Revoke an authentication token, identified by its ID."""
    session = g.db.session('relengapi')
    Token.query.filter_by(id=token_id).delete()
    session.commit()
    return None, 204


@principal.identity_loader
def token_loader():
    header = request.headers.get('Authentication')
    if not header:
        return
    header = header.split()
    if len(header) != 2 or header[0].lower() != 'bearer':
        return
    token_str = header[1]
    try:
        token_info = current_app.tokenauth_serializer.loads(token_str)
    except BadData:
        logger.warning("Got invalid signature in token %r", token_str)
        return None
    if token_info['v'] != TOKENAUTH_VERSION:
        return None
    token_data = Token.query.filter_by(id=token_info['id']).first()
    if token_data:
        identity = Identity(token_data.id, 'token')
        identity.provides.update(set(token_data.actions))
        logger.debug("Access by %r: %s", token_str, identity)
        return identity


@bp.record
def init_blueprint(state):
    app = state.app
    app.tokenauth_serializer = JSONWebSignatureSerializer(app.secret_key)
