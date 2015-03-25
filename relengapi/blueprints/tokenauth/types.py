# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types

from datetime import datetime
from relengapi.lib.api import jsonObject


class JsonToken(wsme.types.Base):

    """A token granting the bearer a limited set of permissions.

    In all cases except creating a new token, the ``token`` attribute is empty.
    There is no way to recover a lost token string except for revoking and
    re-issuing the token.
    """

    _name = 'Token'

    #: token type (short string).  This defaults to ``prm`` for backward
    #: compatibility, but should always be specified.
    typ = wsme.types.wsattr(
        wsme.types.Enum(unicode, 'prm', 'tmp', 'usr'),
        mandatory=False,
        default='prm')

    #: token ID for revokable tokens
    id = wsme.types.wsattr(int, mandatory=False)

    #: not-before time for limited-duration tokens (see
    #: :ref:`Datetime-Format` for format information)
    not_before = wsme.types.wsattr(datetime, mandatory=False)

    #: expiration time for limited-duration tokens
    expires = wsme.types.wsattr(datetime, mandatory=False)

    #: metadata fro limited-duration tokens (arbitrary JSON object)
    metadata = wsme.types.wsattr(jsonObject, mandatory=False)

    #: if true, the token is disabled because the associated user's
    #: permissions are no longer sufficient.
    disabled = wsme.types.wsattr(bool, mandatory=False)

    #: list of permissions this token grants
    permissions = wsme.types.wsattr([unicode], mandatory=True)

    #: the user-supplied token description for revokable tokens
    description = wsme.types.wsattr(unicode, mandatory=False)

    #: user email for user-associated tokens
    user = wsme.types.wsattr(unicode, mandatory=False)

    #: client id for client-associated tokens
    client_id = wsme.types.wsattr(int, mandatory=False)

    #: the opaque token string (only set on new tokens)
    token = wsme.types.wsattr(unicode, mandatory=False)
