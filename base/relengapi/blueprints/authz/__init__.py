# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi.util import make_support_class
from flask import Blueprint
from flask import g
from relengapi import apimethod


bp = Blueprint('authz', __name__, template_folder='templates')


@bp.route("/permitted")
@apimethod()
def permitted():
    """List the permissions the current user has."""
    return sorted('.'.join(a) for a in g.identity.provides)


@bp.record
def init_blueprint(state):
    app = state.app

    permission_mechanisms = {
        'static': ('.static_permissions', 'StaticPermissions'),
        'ldap-groups': ('.ldap_groups', 'LdapGroups'),
    }
    app.permissions = make_support_class(app, __name__, permission_mechanisms,
                                         'RELENGAPI_PERMISSIONS',
                                         'static')
