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
from flask.ext.login import login_required
from flask.ext.login import current_user
from relengapi import p
from relengapi import apimethod
from relengapi.lib import permissions
from relengapi.lib import auth
from itsdangerous import JSONWebSignatureSerializer, BadData
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

TOKENAUTH_VERSION = 1
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


class Token(db.declarative_base('relengapi')):
    __tablename__ = 'auth_tokens'

    def __init__(self, permissions=None, **kwargs):
        kwargs['_permissions'] = ','.join((str(a) for a in permissions or []))
        super(Token, self).__init__(**kwargs)

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.Text, nullable=False)
    _permissions = sa.Column(sa.Text, nullable=False)

    def to_json(self):
        return dict(id=self.id, description=self.description,
                    permissions=[str(a) for a in self.permissions])

    @property
    def permissions(self):
        token_permissions = [p.get(permissionstr)
                             for permissionstr in self._permissions.split(',')]
        # silently ignore any nonexistent permissions; this allows us to remove unused
        # permissions without causing tokens permitting those permissions to fail
        # completely
        return [a for a in token_permissions if a]


class TokenUser(auth.BaseUser):

    type = 'token'

    def __init__(self, token_id, permissions):
        self.token_id = token_id
        self._permissions = permissions

    def get_id(self):
        return 'token:#%s' % self.token_id

    def get_permissions(self):
        return self._permissions


@bp.route('/')
@login_required
def root():
    available_permissions = sorted((str(a), a.__doc__)
                                   for a in current_user.permissions)
    return render_template('new-token.html',
                           available_permissions=available_permissions)


@bp.route('/tokens')
@apimethod()
@p.base.tokens.view.require()
def list_tokens():
    """Get the list of all tokens.  Note that the response does not include the
    actual token strings."""
    return [t.to_json() for t in Token.query.all()]


@bp.route('/tokens', methods=['POST'])
@apimethod()
@p.base.tokens.issue.require()
def issue_token():
    """Issue a new authentication token.  The POST body must contain JSON with keys
    'permissions', a list of allowed permissions; and description, a description of the token."""
    requested_permissions = [p.get(a) for a in request.json['permissions']]
    # ensure the request is for a subset of the permissions the user can
    # perform
    if None in requested_permissions or not set(requested_permissions) <= current_user.permissions:
        raise BadRequest("bad permissions")
    if 'description' not in request.json:
        raise BadRequest("no description")

    session = g.db.session('relengapi')
    token_row = Token(
        description=request.json['description'],
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    token = current_app.tokenauth_serializer.dumps(
        {'v': TOKENAUTH_VERSION, 'id': token_row.id})
    return {'token': token}


@bp.route('/tokens/<int:token_id>')
@apimethod()
@p.base.tokens.view.require()
def get_token(token_id):
    """Get a token, identified by its ID."""
    token_data = Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound
    return token_data.to_json()


@bp.route('/tokens/query', methods=['POST'])
@apimethod()
@p.base.tokens.view.require()
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
@p.base.tokens.revoke.require()
def revoke_token(token_id):
    """Revoke an authentication token, identified by its ID."""
    session = g.db.session('relengapi')
    Token.query.filter_by(id=token_id).delete()
    session.commit()
    return None, 204


@auth.request_loader
def token_loader(request):
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
        user = TokenUser(token_data.id, token_data.permissions)
        logger.debug("Token access by %s", user)
        return user


@bp.record
def init_blueprint(state):
    app = state.app
    if not app.secret_key:
        logger.warning("The `SECRET_KEY` setting is not set; tokens will be signed with "
                       "an insecure, static key")
    secret_key = app.secret_key or 'NOT THAT SECRET'
    app.tokenauth_serializer = JSONWebSignatureSerializer(secret_key)
