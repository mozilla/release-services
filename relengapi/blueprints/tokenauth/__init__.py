# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import logging
import sqlalchemy as sa
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

p.base.tokens.prm.view.doc('See permanent token metadata')
p.base.tokens.prm.issue.doc('Issue new permanent tokens')
p.base.tokens.prm.revoke.doc('Revoke permanent tokens')

p.base.tokens.usr.view.all.doc('See all user token metadata')
p.base.tokens.usr.view.my.doc('See user token metadata for my tokens')
p.base.tokens.usr.issue.doc('Issue new user tokens')
p.base.tokens.usr.revoke.all.doc('Revoke any user token')
p.base.tokens.usr.revoke.my.doc('Revoke user tokens issued by me')

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
    # TODO: client_id

    if user.token_data:
        td = user.token_data
        attrs['id'] = td.id
        attrs['description'] = td.description
        attrs['permissions'] = [str(p) for p in td.permissions]
        if td.user:
            attrs['user'] = td.user

    return types.JsonToken(**attrs)


def get_user_email():
    try:
        return current_user.authenticated_email
    except AttributeError:
        return None


def can_access_token(access, typ, user):
    # ensure the user can see this token; for non-user-associated
    # tokens, that's just a permission check
    if typ in ('prm',):
        if not p.get('base.tokens.{}.{}'.format(typ, access)).can():
            return False
    # for user-associated tokens, if the .all permission is set,
    # the access is fine; otherwise very that the user matches and
    # the .my permission is set.
    elif typ in ('usr',):
        if not p.get('base.tokens.{}.{}.all'.format(typ, access)).can():
            email = get_user_email()
            if not email or not user or user != email:
                return False
            if not p.get('base.tokens.{}.{}.my'.format(typ, access)).can():
                return False

    return True


@bp.route('/')
@login_required
def root():
    return angular.template('tokens.html',
                            url_for('.static', filename='tokens.js'),
                            tokens=api.get_data(list_tokens))


@bp.route('/tokens')
@apimethod([types.JsonToken], unicode)
def list_tokens(typ=None):
    """Get a list of all unlimited-duration tokens the user has permisison to
    see.

    With ``?typ=..``, limit to tokens of that type.

    Note that the response does not include the actual token strings.
    Such strings are only revealed when creating a new token."""
    tbl = tables.Token
    email = get_user_email()

    cond = []
    if p.base.tokens.prm.view.can():
        cond.append(tbl.typ == 'prm')
    if p.base.tokens.usr.view.all.can():
        cond.append(tbl.typ == 'usr')
    elif email and p.base.tokens.usr.view.my.can():
        cond.append(sa.and_(tbl.typ == 'usr',
                            tbl.user == email))
    if not cond:
        return []
    cond = sa.or_(*cond)
    if typ:
        cond = sa.and_(cond, tbl.typ == typ)

    q = tables.Token.query.filter(cond)
    return [t.to_jsontoken() for t in q.all()]


token_issuers = {}
token_issuer = lambda typ: lambda fn: token_issuers.__setitem__(typ, fn)


@token_issuer('prm')
def issue_prm(body, requested_permissions):
    session = g.db.session('relengapi')
    token_row = tables.Token(
        typ='prm',
        description=body.description,
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    rv = token_row.to_jsontoken()
    rv.token = tokenstr.claims_to_str(
        {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % token_row.id})
    return rv


@token_issuer('tmp')
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


@token_issuer('usr')
def issue_usr(body, requested_permissions):
    email = get_user_email()
    if not email:
        raise Forbidden("Authenticate with a user-related "
                        "mechanism to issue user tokens")

    session = g.db.session('relengapi')
    token_row = tables.Token(
        typ='usr',
        user=email,
        description=body.description,
        permissions=requested_permissions)
    session.add(token_row)
    session.commit()

    rv = token_row.to_jsontoken()
    rv.token = tokenstr.claims_to_str(
        {'iss': 'ra2', 'typ': 'usr', 'jti': 't%d' % token_row.id})
    return rv

required_token_attributes = {
    'prm': ['permissions', 'description'],
    'tmp': ['permissions', 'not_before', 'expires', 'metadata'],
    'usr': ['permissions', 'description'],
}


@bp.route('/tokens', methods=['POST'])
@apimethod(types.JsonToken, body=types.JsonToken)
def issue_token(body):
    """Issue a new token.  The body should not include a ``token`` or ``id``,
    but should include a ``typ`` and the necessary fields for that type.  The
    response will contain both ``token`` and ``id``.  You must have permission
    to issue the given token type."""
    typ = body.typ

    # verify permission to issue this type
    perm = p.get('base.tokens.{}.issue'.format(typ))
    if not perm.can():
        raise Forbidden("You do not have permission to create this token type")

    # verify required parameters; any extras will be ignored
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
def get_token(token_id):
    """Get a token, identified by its ``id``."""
    token_data = tables.Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise NotFound

    if not can_access_token('view', token_data.typ, token_data.user):
        raise NotFound

    return token_data.to_jsontoken()


@bp.route('/tokens/query', methods=['POST'])
@apimethod(types.JsonToken, body=unicode)
def query_token(body):
    """Get a token, specified by the token key given in the request body
    (this avoids embedding a token in a URL, where it might be logged)return .

    The caller must have permission to view this type of token, unless
    the token is limited-duration (in which case the API is simply
    decoding the JSON web token anyway)."""
    # use the token loader to interpret the token
    user = loader.token_loader.from_str(body)
    if not user:
        raise NotFound

    if not can_access_token('view',
                            user.claims['typ'],
                            getattr(user, 'authenticated_email', None)):
        raise Forbidden

    return user_to_jsontoken(user)


@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
@apimethod(None, int)
def revoke_token(token_id):
    """Revoke an authentication token, identified by its ID.

    The caller must have permission to revoke this type of token; if
    that is a ``.my`` permission, then the user email must match.

    The response status is 204 on success.  Revoking an already-revoked token
    returns 403."""
    session = g.db.session('relengapi')
    token_data = tables.Token.query.filter_by(id=token_id).first()
    # don't leak info about which tokens exist -- return the same
    # status whether the token is missing or permission is missing
    if not token_data:
        raise Forbidden

    if not can_access_token('revoke', token_data.typ, token_data.user):
        raise Forbidden

    tables.Token.query.filter_by(id=token_id).delete()
    session.commit()
    return None, 204


# enable the loader to get a look at each incoming request
auth.request_loader(loader.token_loader)


@bp.record
def init_blueprint(state):
    tokenstr.init_app(state.app)
