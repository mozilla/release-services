# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from relengapi.blueprints.tokenauth import tables
from relengapi.blueprints.tokenauth import tokenstr
from relengapi.lib import auth

logger = logging.getLogger(__name__)


class TokenUser(auth.BaseUser):

    type = 'token'

    def __init__(self, token_id, permissions):
        self.token_id = token_id
        self._permissions = set(permissions)

    def get_id(self):
        return 'token:#%s' % self.token_id

    def get_permissions(self):
        return self._permissions


def token_loader(request):
    # extract the token from the headers, returning None if anything's
    # wrong
    header = request.headers.get('Authentication')
    if not header:
        return
    header = header.split()
    if len(header) != 2 or header[0].lower() != 'bearer':
        return
    claims = tokenstr.str_to_claims(header[1])
    if not claims:
        return

    token_data = tables.Token.query.filter_by(id=claims['id']).first()
    if token_data:
        user = TokenUser(token_data.id, token_data.permissions)
        logger.debug("Token access by %s", user)
        return user
