# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from relengapi.lib import angular
from relengapi.lib import permissions
from relengapi.lib.api import apimethod

bp = Blueprint('auth', __name__,
               template_folder='templates',
               static_folder='static')
bp.root_widget_template('auth_root_widget.html', priority=-100)


@bp.route("/")
def account():
    """Show the user information about their account"""
    perms = [permissions.JsonPermission(name='.'.join(p), doc=p.__doc__)
             for p in current_user.permissions]
    authenticated_email = current_user.authenticated_email if current_user.type == 'human' else None
    return angular.template("account.html",
                            url_for('.static', filename='account.js'),
                            authenticated_email=authenticated_email,
                            permissions=perms)


@bp.route("/permissions")
@login_required
@apimethod([permissions.JsonPermission])
def perms():
    return [permissions.JsonPermission(name='.'.join(p), doc=p.__doc__)
            for p in current_user.permissions]
