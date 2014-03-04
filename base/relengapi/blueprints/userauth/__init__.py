# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import render_template
from flask_login import login_required
from relengapi import login_manager
from relengapi import browser_id
from flask.ext.login import UserMixin


bp = Blueprint('userauth', __name__, template_folder='templates')

# configure the login manager
login_manager.login_view = 'userauth.login_request'
login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
login_manager.get_user = lambda user_id: login_manager.user_callback(user_id)


class User(UserMixin):

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return unicode(self.authenticated_email)


@login_manager.user_loader
def login_manager_user_loader(authenticated_email):
    return User(authenticated_email)


@browser_id.user_loader
def browser_id_user_loader(login_info):
    if login_info['status'] != 'okay':
        return None
    return User(login_info['email'])

@bp.route("/account")
@login_required
def account():
    return render_template("account.html")
