# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import request
from relengapi import db
import sqlalchemy as sa
from flask.ext.principal import Identity
from relengapi.principal import actions

class Token(db.declarative_base('relengapi')):
    __tablename__ = 'tokens'

    id = sa.Column(sa.Integer, primary_key=True)
    expires = sa.Column(sa.DateTime)
    issued_by = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    _actions = sa.Column(sa.Text, nullable=False)

    @property
    def actions(self):
        token_actions = [actions.get(actionstr) for actionstr in self._actions.split()]
        # silently ignore any nonexistent actions
        return filter(None, token_actions)

actions.base.tokens.view.doc('See authentication token metadata')
actions.base.tokens.issue.doc('Issue new authentication tokens')
actions.base.tokens.revoke.doc('Revoke authentication tokens')

tokens = {
    'abcd': [actions.test1],
}

def init_app(app):
    @app.principal.identity_loader
    def token_loader():
        token = request.headers.get('X-Relengapi-Token')
        if not token:
            return
        if token in tokens:
            identity = Identity(token, 'token')
            identity.provides.update(set(tokens[token]))
            return identity
