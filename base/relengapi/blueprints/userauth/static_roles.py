# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.principal import identity_loaded, RoleNeed

class StaticRoles(object):

    def __init__(self, app):

        roles_map = app.config.get('RELENGAPI_ROLES', {}).get('roles', {})

        @identity_loaded.connect_via(app)
        def on_identity_loaded(sender, identity):
            for role in roles_map.get(identity.id, []):
                identity.provides.add(RoleNeed(role))

