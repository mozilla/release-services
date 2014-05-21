# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
from flask.ext.principal import identity_loaded
from relengapi import actions

class StaticActions(object):

    def __init__(self, app):

        actions_map = app.config.get('RELENGAPI_ACTIONS', {}).get('actions', {})

        # verify that each specified action exists
        for actionstr in set(itertools.chain(*actions_map.values())):
            try:
                actions[actionstr]
            except KeyError:
                raise RuntimeError("invalid static action in settings: %r" % (actionstr,))

        @identity_loaded.connect_via(app)
        def on_identity_loaded(sender, identity):
            # only attach identities for actual user logins; others are handled separately
            if identity.auth_type != 'user':
                return
            for actionstr in actions_map.get(identity.id, []):
                identity.provides.add(actions[actionstr])
