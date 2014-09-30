# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import sqlalchemy as sa
import wsme.types

from flask import Blueprint
from flask import current_app
from flask import g
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_required
from itsdangerous import BadData
from itsdangerous import JSONWebSignatureSerializer
from relengapi import apimethod
from relengapi import p
from relengapi.lib import angular
from relengapi.lib import api
from relengapi.lib import auth
from relengapi.lib import db
from relengapi.lib import permissions
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

    def to_jsontoken(self):
        return JsonToken(id=self.id, description=self.description,
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


class JsonToken(wsme.types.Base):
    """A token granting the bearer a limited set of permissions.

    In all cases except creating a new token, the ``token`` attribute is empty.
    There is no way to recover a lost token string except for revoking and
    re-issuing the token.
    """

    _name = 'Token'

    #: token ID
    id = wsme.types.wsattr(int, mandatory=False)

    #: the opaque token string (only set on new tokens)
    token = wsme.types.wsattr(unicode, mandatory=False)

    #: the user-supplied token description
    description = wsme.types.wsattr(unicode, mandatory=True)

    #: list of permissions this token grants
    permissions = wsme.types.wsattr([unicode], mandatory=True)


@bp.route('/')
@login_required
def root():
    return angular.template('tokens.html',
                            url_for('.static', filename='tokens.js'),
                            tokens=api.get_data(list_tokens))


@bp.route('/tokens')
@p.base.tokens.view.require()
@apimethod([JsonToken])
def list_tokens():
    """Get a list of all existing tokens.

    Note that the response does not include the actual token strings.
    Such strings are only revealed when creating a new token."""
    return [t.to_jsontoken() for t in Token.query.all()]


@bp.route('/tokens', methods=['POST'])
@apimethod(JsonToken, body=JsonToken)
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
    token_row = Token(
        description=body.description,
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    token = current_app.tokenauth_serializer.dumps(
        {'v': TOKENAUTH_VERSION, 'id': token_row.id})
    rv = token_row.to_jsontoken()
    rv.token = token
    return rv


@bp.route('/tokens/<int:token_id>')
@apimethod(JsonToken, int)
@p.base.tokens.view.require()
def get_token(token_id):
    """Get a token, identified by its ``id``."""
    token_data = Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound
    return token_data.to_jsontoken()


@bp.route('/tokens/query', methods=['POST'])
@p.base.tokens.view.require()
@apimethod(JsonToken, body=unicode)
def get_token_by_token(body):
    """Get a token, specified by the token key given in the request body
    (this avoids embedding a token in a URL, where it might be logged)."""
    token_str = body
    try:
        token_info = current_app.tokenauth_serializer.loads(token_str)
    except BadData:
        raise NotFound
    if token_info['v'] != TOKENAUTH_VERSION:
        raise NotFound
    token_data = Token.query.filter_by(id=token_info['id']).first()
    if not token_data:
        raise NotFound
    return token_data.to_jsontoken()


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@apimethod(None, int)
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
