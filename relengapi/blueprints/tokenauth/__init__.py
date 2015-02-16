# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import logging
import wsme

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
from relengapi.util import tz
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotFound

logger = logging.getLogger(__name__)
bp = Blueprint('tokenauth', __name__,
               template_folder='templates',
               static_folder='static')

p.base.tokens.prm.issue.doc('Issue new permanent authentication tokens')
p.base.tokens.prm.view.doc('See permanent token metadata')
p.base.tokens.prm.revoke.doc('Revoke permanent authentication tokens')

p.base.tokens.tmp.issue.doc('Issue new temporary authentication tokens')


def permitted():
    return permissions.can(
        p.base.tokens.prm.view,
        p.base.tokens.prm.issue,
        p.base.tokens.prm.revoke,
        p.base.tokens.tmp.issue)
bp.root_widget_template(
    'tokenauth_root_widget.html', priority=100, condition=permitted)


def user_to_jsontoken(user):
    attrs = {}
    cl = user.claims
    attrs['typ'] = user.claims['typ']
    if 'nbf' in cl:
        attrs['not_before'] = tz.utcfromtimestamp(cl['nbf'])
    if 'exp' in cl:
        attrs['expires'] = tz.utcfromtimestamp(cl['exp'])
    if 'mta' in cl:
        attrs['metadata'] = cl['mta']
    if 'prm' in cl:
        attrs['permissions'] = cl['prm']
    # TODO: user, client_id

    if user.token_data:
        td = user.token_data
        attrs['id'] = td.id
        attrs['description'] = td.description
        attrs['permissions'] = [str(p) for p in td.permissions]

    return types.JsonToken(**attrs)


@bp.route('/')
@login_required
def root():
    return angular.template('tokens.html',
                            url_for('.static', filename='tokens.js'),
                            tokens=api.get_data(list_tokens))


@bp.route('/tokens')
@apimethod([types.JsonToken])
def list_tokens():
    """Get a list of all existing tokens the user has permisison to see.

    Note that the response does not include the actual token strings.
    Such strings are only revealed when creating a new token."""
    if p.base.tokens.prm.view.can():
        return [t.to_jsontoken() for t in tables.Token.query.all()]
    return []


def issue_prm(body, requested_permissions):
    session = g.db.session('relengapi')
    token_row = tables.Token(
        description=body.description,
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    rv = token_row.to_jsontoken()
    rv.token = tokenstr.claims_to_str(
        {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % token_row.id})
    return rv


def issue_tmp(body, requested_permissions):
    nbf = calendar.timegm(body.not_before.utctimetuple())
    exp = calendar.timegm(body.expires.utctimetuple())
    perm_strs = [str(prm) for prm in requested_permissions]
    token = tokenstr.claims_to_str({
        'iss': 'ra2',
        'typ': 'tmp',
        'nbf': nbf,
        'exp': exp,
        'prm': perm_strs,
        'mta': body.metadata,
    })
    return types.JsonToken(typ='tmp', token=token,
                           not_before=body.not_before,
                           expires=body.expires,
                           permissions=perm_strs,
                           metadata=body.metadata)

token_issuers = {
    'prm': issue_prm,
    'tmp': issue_tmp,
}

required_token_attributes = {
    'prm': ['permissions', 'description'],
    'tmp': ['permissions', 'not_before', 'expires', 'metadata'],
}


@bp.route('/tokens', methods=['POST'])
@apimethod(types.JsonToken, body=types.JsonToken)
@p.base.tokens.prm.issue.require()
def issue_token(body):
    """Issue a new token.  The body should not include a ``token`` or ``id``,
    but should include a ``typ`` and the necessary fields for that type.  The
    response will contain both ``token`` and ``id``.  You must have permission
    to issue the given token type."""
    # verify required parameters; any extras will be ignored
    typ = body.typ
    for attr in required_token_attributes[typ]:
        if getattr(body, attr) is wsme.Unset:
            raise BadRequest("missing %s" % attr)

    # All types have permissions, so handle those here -- ensure the request is
    # for a subset of the permissions the user can perform
    requested_permissions = [p.get(a) for a in body.permissions]
    if None in requested_permissions:
        raise BadRequest("bad permissions")
    if not set(requested_permissions) <= current_user.permissions:
        raise BadRequest("bad permissions")

    # Dispatch the rest to the per-type function
    return token_issuers[typ](body, requested_permissions)


@bp.route('/tokens/<int:token_id>')
@apimethod(types.JsonToken, int)
@p.base.tokens.prm.view.require()
def get_token(token_id):
    """Get a token, identified by its ``id``."""
    token_data = tables.Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound
    return token_data.to_jsontoken()


@bp.route('/tokens/query', methods=['POST'])
@apimethod(types.JsonToken, body=unicode)
def get_token_by_token(body):
    """Get a token, specified by the token key given in the request body
    (this avoids embedding a token in a URL, where it might be logged).

    The caller must have permission to view this type of token, unless
    the token is limited-duration (in which case the API is simply
    decoding the JSON web token anyway)."""
    user = loader.token_loader.from_str(body)
    if not user:
        raise NotFound
    typ = user.claims['typ']
    # verify this user can view this token type
    any_can_view = typ in ('tmp',)
    if any_can_view or p.get('base.tokens.{}.view'.format(typ)).can():
        return user_to_jsontoken(user)
    raise Forbidden


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@apimethod(None, int)
@p.base.tokens.prm.revoke.require()
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
