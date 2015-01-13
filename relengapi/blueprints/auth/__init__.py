# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_required
from relengapi.lib import angular
from relengapi.lib import permissions
from relengapi.lib.api import apimethod

bp = Blueprint('auth', __name__,
               template_folder='templates',
               static_folder='static')


@bp.route("/")
def account():
    """Show the user information about their account"""
    return angular.template("account.html",
                            url_for('.static', filename='account.js'))


@bp.route("/permissions")
@login_required
@apimethod([permissions.JsonPermission])
def user_permissions():
    return [permissions.JsonPermission(name='.'.join(p), doc=p.__doc__)
            for p in current_user.permissions]
