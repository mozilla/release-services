# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa

from relengapi import p
from relengapi.blueprints.tokenauth import types
from relengapi.lib import db


class Token(db.declarative_base('relengapi')):
    __tablename__ = 'auth_tokens'

    def __init__(self, permissions=None, **kwargs):
        kwargs['_permissions'] = ','.join((str(a) for a in permissions or []))
        super(Token, self).__init__(**kwargs)

    id = sa.Column(sa.Integer, primary_key=True)
    typ = sa.Column(sa.String(4), nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    user = sa.Column(sa.Text, nullable=True)
    _permissions = sa.Column(sa.Text, nullable=False)

    def to_jsontoken(self):
        return types.JsonToken(id=self.id, description=self.description,
                               permissions=[str(a) for a in self.permissions])

    @property
    def permissions(self):
        token_permissions = [p.get(permissionstr)
                             for permissionstr in self._permissions.split(',')]
        # silently ignore any nonexistent permissions; this allows us to remove unused
        # permissions without causing tokens permitting those permissions to fail
        # completely
        return [a for a in token_permissions if a]
