# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import calendar
import datetime
import time

import dateutil.parser
import flask
import flask_login
import pytz
import sqlalchemy as sa
import werkzeug.exceptions

import backend_common.auth
import cli_common.log
import releng_tokens.config
import releng_tokens.models

logger = cli_common.log.get_logger(__name__)


def initial_data():
    initial_data = backend_common.auth.initial_data()
    initial_data['tokens'] = list_tokens()['result']
    return initial_data


def can_access_token(access, typ):
    # ensure the user can see this token; for non-user-associated
    # tokens, that's just a permission check
    if typ in ('prm',):
        permission = '{}/{}/{}'.format(releng_tokens.config.SCOPE_PREFIX, typ, access)
        if not flask_login.current_user.has_permissions(permission):
            return False

    # for user-associated tokens, if the .all permission is set,
    # the access is fine; otherwise very that the user matches and
    # the .my permission is set.
    elif typ in ('usr',):
        permission = '{}/{}/{}/all'.format(releng_tokens.config.SCOPE_PREFIX, typ, access)
        if not flask_login.current_user.has_permissions(permission):
            permission = '{}/{}/{}/my'.format(releng_tokens.config.SCOPE_PREFIX, typ, access)
            if not flask_login.current_user.has_permissions(permission):
                return False

    return True


def list_tokens(typ=None):
    tbl = releng_tokens.models.Token

    conds = []
    if flask_login.current_user.has_permissions(releng_tokens.config.SCOPE_PREFIX + '/prm/view'):
        conds.append(tbl.typ == 'prm')
    if flask_login.current_user.has_permissions(releng_tokens.config.SCOPE_PREFIX + '/usr/view/all'):
        conds.append(tbl.typ == 'usr')
    elif flask_login.current_user.has_permissions(releng_tokens.config.SCOPE_PREFIX + '/usr/view/my'):
        conds.append(sa.and_(tbl.typ == 'usr',
                             tbl.user == flask_login.current_user.get_id()))
    if not conds:
        return dict(result=[])
    disjunction = sa.or_(*conds)
    if typ:
        filter_cond = sa.and_(disjunction, tbl.typ == typ)
    else:
        filter_cond = disjunction

    q = releng_tokens.models.Token.query.filter(filter_cond)
    return dict(result=[t.to_dict() for t in q.all()])


token_issuers = {}


def token_issuer(typ):
    def wrapper(fn):
        token_issuers.__setitem__(typ, fn)
    return wrapper


@token_issuer('prm')
def issue_prm(body, requested_permissions):
    session = flask.current_app.db.session
    token_row = releng_tokens.models.Token(
        typ='prm',
        description=body['description'],
        permissions=requested_permissions,
        disabled=False)
    session.add(token_row)
    session.commit()

    rv = token_row.to_dict()
    rv['token'] = backend_common.auth.claims_to_str(
        {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % token_row.id})
    return rv


@token_issuer('tmp')
def issue_tmp(body, requested_permissions):
    if 'not_before' in body:
        raise werkzeug.exceptions.BadRequest('do not specify not_before when creating a tmp token')
    nbf = int(time.time())
    expires = dateutil.parser.parse(body['expires'])
    exp = calendar.timegm(expires.utctimetuple())
    if exp <= nbf:
        raise werkzeug.exceptions.BadRequest('expiration time must be in the future')
    max_lifetime = flask.current_app.config.get(
        'RELENGAPI_TMP_TOKEN_MAX_LIFETIME', 86400)
    if exp > nbf + max_lifetime:
        raise werkzeug.exceptions.BadRequest(
            'expiration time is more than %d seconds in the future' % max_lifetime)
    perm_strs = [str(prm) for prm in requested_permissions]
    token = backend_common.auth.claims_to_str({
        'iss': 'ra2',
        'typ': 'tmp',
        'nbf': nbf,
        'exp': exp,
        'prm': perm_strs,
        'mta': body['metadata'],
    })
    return dict(
        typ='tmp',
        token=token,
        not_before=datetime.datetime.utcfromtimestamp(nbf).replace(tzinfo=pytz.UTC),
        expires=expires,
        permissions=perm_strs,
        metadata=body['metadata'],
        disabled=False,
    )


@token_issuer('usr')
def issue_usr(body, requested_permissions):
    session = flask.current_app.db.session
    token_row = releng_tokens.models.Token(
        typ='usr',
        user=flask_login.current_user.get_id(),
        description=body['description'],
        permissions=requested_permissions,
        disabled=False)
    session.add(token_row)
    session.commit()

    rv = token_row.to_dict()
    rv['token'] = backend_common.auth.claims_to_str(
        {'iss': 'ra2', 'typ': 'usr', 'jti': 't%d' % token_row.id})
    return rv


UNSET = object()
required_token_attributes = {
    'prm': ['permissions', 'description'],
    'tmp': ['permissions', 'expires', 'metadata'],
    'usr': ['permissions', 'description'],
}


def issue_token(body):
    '''Issue a new token.  The body should not include a ``token`` or ``id``,
    but should include a ``typ`` and the necessary fields for that type.  The
    response will contain both ``token`` and ``id``.  You must have permission
    to issue the given token type.'''
    typ = body['typ']

    # verify permission to issue this type
    permission = '{}/{}/issue'.format(releng_tokens.config.SCOPE_PREFIX, typ)
    if not flask_login.current_user.has_permissions(permission):
        raise werkzeug.exceptions.Forbidden(
            'You do not have permission to create this token type')

    # verify required parameters; any extras will be ignored
    for attr in required_token_attributes[typ]:
        if body.get(attr, UNSET) is UNSET:
            raise werkzeug.exceptions.BadRequest('missing %s' % attr)

    # prohibit silly requests
    if body.get('disabled'):
        raise werkzeug.exceptions.BadRequest('can\'t issue disabled tokens')

    # All types have permissions, so handle those here -- ensure the request is
    # for a subset of the permissions the user can perform
    all_relengapi_permissions = [
        (i, backend_common.auth.from_relengapi_permission(i))
        for i in backend_common.auth.RELENGAPI_PERMISSIONS.keys()
    ]
    requested_permissions = [
        old
        for old, new in all_relengapi_permissions
        if flask_login.current_user.has_permissions(new) and old in body.get('permissions', [])
    ]

    if None in requested_permissions:
        raise werkzeug.exceptions.BadRequest('bad permissions')
    if not set(requested_permissions) <= set([i for i, j in all_relengapi_permissions]):
        raise werkzeug.exceptions.BadRequest('bad permissions')

    # Dispatch the rest to the per-type function.  Note that WSME has already
    # ensured `typ` is one of the recognized types.
    token = token_issuers[typ](body, requested_permissions)
    perms_str = ', '.join(str(p) for p in requested_permissions)
    log = logger.bind(token_typ=token['typ'], token_permissions=perms_str, mozdef=True)
    if token.get('id'):
        log = log.bind(token_id=token['id'])
    log.info('Issuing {} token to {} with permissions {}'.format(
        token['typ'], flask_login.current_user, perms_str))
    return dict(result=token)


def get_token(token_id):
    '''Get a token, identified by its ``id``.'''
    token_data = releng_tokens.models.Token.query.filter_by(id=token_id).first()
    if not token_data:
        raise werkzeug.exceptions.NotFound

    if not can_access_token('view', token_data.typ):
        raise werkzeug.exceptions.NotFound

    return token_data.to_dict()


def query_token(body):
    '''Get a token, specified by the token key given in the request body
    (this avoids embedding a token in a URL, where it might be logged).

    The caller must have permission to view this type of token, unless
    the token is limited-duration (in which case the API is simply
    decoding the JSON web token anyway).'''
    # use the token loader to interpret the token
    user = backend_common.auth.user_from_str(body)
    if not user:
        raise werkzeug.exceptions.NotFound

    if not can_access_token('view', user.claims['typ']):
        raise werkzeug.exceptions.Forbidden

    return backend_common.auth.user_to_jsontoken(user)


def revoke_token(id):
    '''Revoke an authentication token, identified by its ID.

    The caller must have permission to revoke this type of token; if
    that is a ``.my`` permission, then the user email must match.

    The response status is 204 on success.  Revoking an already-revoked token
    returns 403.'''
    session = flask.current_app.db.session
    token_data = releng_tokens.models.Token.query.filter_by(id=id).first()
    # don't leak info about which tokens exist -- return the same
    # status whether the token is missing or permission is missing
    if not token_data:
        raise werkzeug.exceptions.Forbidden

    if not can_access_token('revoke', token_data.typ):
        raise werkzeug.exceptions.Forbidden

    perms_str = ', '.join(str(p) for p in token_data.permissions)
    log = logger.bind(token_typ=token_data.typ, token_permissions=perms_str,
                      token_id=id, mozdef=True)
    log.info('Revoking {} token #{} with permissions {}'.format(
        token_data.typ, token_data.id, perms_str))

    releng_tokens.models.Token.query.filter_by(id=id).delete()
    session.commit()
    return None, 204
