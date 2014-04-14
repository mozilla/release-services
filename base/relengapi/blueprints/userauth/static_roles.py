# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
from flask.ext.principal import identity_loaded
from relengapi.principal import roles

class StaticRoles(object):

    def __init__(self, app):

        roles_map = app.config.get('RELENGAPI_ROLES', {}).get('roles', {})

        # verify that each specified role exists
        for rolestr in set(itertools.chain(*roles_map.values())):
            try:
                roles[rolestr]
            except KeyError:
                raise RuntimeError("invalid static role in settings: %r" % (rolestr,))

        @identity_loaded.connect_via(app)
        def on_identity_loaded(sender, identity):
            for rolestr in roles_map.get(identity.id, []):
                identity.provides.add(roles[rolestr])

