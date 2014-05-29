# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
from relengapi import p


class StaticPermissions(object):

    def __init__(self, app):

        permissions_map = app.config.get('RELENGAPI_PERMISSIONS', {}).get('permissions', {})

        # verify that each specified permission exists
        for perm in set(itertools.chain(*permissions_map.values())):
            try:
                p[perm]
            except KeyError:
                raise RuntimeError("invalid static permission in settings: %r" % (perm,))

        def on_identity_loaded(sender, identity):
            # only attach identities for actual user logins; others are handled separately
            if identity.auth_type != 'user':
                return
            for perm in permissions_map.get(identity.id, []):
                identity.provides.add(p[perm])
