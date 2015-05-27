# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools

from functools import partial
from relengapi import p
from relengapi.lib.auth import base
from relengapi.lib.auth import permissions_stale


class StaticAuthz(base.BaseAuthz):

    def __init__(self, permissions_map):
        self.permissions_map = permissions_map

    def get_user_permissions(self, email):
        if email not in self.permissions_map:
            return None
        return set(p[perm] for perm in self.permissions_map[email])


def on_permissions_stale(permissions_map, sender, user, permissions):
    for perm in permissions_map.get(user.authenticated_email, []):
        permissions.add(p[perm])


def init_app(app):
    permissions_map = app.config.get(
        'RELENGAPI_PERMISSIONS', {}).get('permissions', {})

    # verify that each specified permission exists
    for perm in set(itertools.chain(*permissions_map.values())):
        try:
            p[perm]
        except KeyError:
            raise RuntimeError(
                "invalid static permission in settings: %r" % (perm,))

    permissions_stale.connect_via(app)(
        partial(on_permissions_stale, permissions_map))

    app.authz = StaticAuthz(permissions_map)
