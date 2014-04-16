# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi.util import make_support_class
from flask import Blueprint
from flask import g
from relengapi import apimethod


bp = Blueprint('authz', __name__, template_folder='templates')

@bp.route("/permitted-actions")
@apimethod()
def permitted_actions():
    """List the actions this identity is permitted to take."""
    return sorted('.'.join(a) for a in g.identity.provides)


@bp.record
def init_blueprint(state):
    app = state.app

    action_mechanisms = {
        'static': ('.static_actions', 'StaticActions'),
    }
    app.actions = make_support_class(app, __name__, action_mechanisms,
                                     'RELENGAPI_ACTIONS',
                                     'static')
