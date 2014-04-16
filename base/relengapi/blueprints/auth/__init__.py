# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import render_template
from flask.ext.login import login_required


bp = Blueprint('auth', __name__, template_folder='templates')


@bp.route("/account")
@login_required
def account():
    """Show the user information about their account"""
    return render_template("account.html")
