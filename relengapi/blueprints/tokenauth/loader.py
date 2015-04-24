# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time

from relengapi import p
from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth import tokenstr
from relengapi.lib import auth

logger = logging.getLogger(__name__)


class TokenUser(auth.BaseUser):

    type = 'token'

    def __init__(self, claims, authenticated_email=None,
                 permissions=[], token_data={}):
        self.claims = claims
        self._permissions = set(permissions)
        self.token_data = token_data
        if authenticated_email:
            self.authenticated_email = authenticated_email

    def get_id(self):
        parts = ['token', self.claims['typ']]
        if 'jti' in self.claims:
            parts.append('id={}'.format(self.claims['jti']))
        try:
            parts.append('user={}'.format(self.authenticated_email))
        except AttributeError:
            pass
        return ':'.join(parts)

    def get_permissions(self):
        return self._permissions


def permlist_to_permissions(permlist):
    token_permissions = [p.get(s) for s in permlist]
    # silently ignore any nonexistent permissions; this allows us to remove unused
    # permissions without causing tokens permitting those permissions to fail
    # completely
    return [perm for perm in token_permissions if perm]


class TokenLoader(object):

    def __init__(self):
        self.type_functions = {}

    def type_function(self, typ):
        def dec(fn):
            assert typ not in self.type_functions, "duplicate type function"
            self.type_functions[typ] = fn
            return fn
        return dec

    def __call__(self, request):
        # extract the token from the headers, returning None if anything's
        # wrong
        header = request.headers.get('Authorization')
        if not header:
            # keep backward compatibility with the old header
            header = request.headers.get('Authentication')
            if not header:
                return
            # see https://github.com/mozilla/build-relengapi/pull/192/files
            logger.warning("client is using 'Authentication' header instead of "
                           "'Authorization'")
        header = header.split()
        if len(header) != 2 or header[0].lower() != 'bearer':
            return
        return self.from_str(header[1])

    def from_str(self, token_str):
        claims = tokenstr.str_to_claims(token_str)
        if not claims:
            return
        try:
            typ_fn = self.type_functions[claims['typ']]
        except KeyError:
            return
        user = typ_fn(claims)
        if user:
            logger.debug("Token access by %s", user)
        return user


token_loader = TokenLoader()
auth.request_loader(token_loader)


@token_loader.type_function('prm')
def prm_loader(claims):
    token_id = tokenstr.jti2id(claims['jti'])
    token_data = tables.Token.query.filter_by(id=token_id).first()
    if token_data:
        assert token_data.typ == 'prm'
        return TokenUser(claims,
                         permissions=token_data.permissions,
                         token_data=token_data)


@token_loader.type_function('tmp')
def tmp_loader(claims):
    # check validity range; note that these claims *must* exist
    now = time.time()
    if now < claims['nbf'] or now > claims['exp']:
        return

    permissions = permlist_to_permissions(claims['prm'])
    return TokenUser(claims, permissions=permissions)


@token_loader.type_function('usr')
def usr_loader(claims):
    token_id = tokenstr.jti2id(claims['jti'])
    token_data = tables.Token.query.filter_by(id=token_id).first()
    if token_data and not token_data.disabled:
        assert token_data.typ == 'usr'
        return TokenUser(claims,
                         permissions=token_data.permissions,
                         token_data=token_data,
                         authenticated_email=token_data.user)


def init_app(app):
    pass
