# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


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
