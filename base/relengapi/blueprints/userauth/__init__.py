# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask_login import login_required
from flask_login import current_user
from relengapi import login_manager
from flask.ext.login import UserMixin


bp = Blueprint('userauth', __name__, template_folder='templates')


class User(UserMixin):

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return unicode(self.authenticated_email)

# login manager

def init_app_login_manager(app):
    @login_manager.user_loader
    def login_manager_user_loader(authenticated_email):
        return User(authenticated_email)

    # configure the login manager to redirect to a bare "please login" page when
    # a login is required
    login_manager.login_view = 'userauth.login_request'
    login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
    login_manager.get_user = lambda user_id: login_manager.user_callback(
        user_id)
    login_manager.init_app(app)

# browserid

def init_app_browserid(app):
    from flask.ext.browserid import BrowserID
    browser_id = BrowserID()

    @browser_id.user_loader
    def browser_id_user_loader(login_info):
        if login_info['status'] != 'okay':
            return None
        return User(login_info['email'])

    # this really shouldn't be app config, but whatever
    app.config['BROWSERID_LOGIN_URL'] = '/userauth/login'
    app.config['BROWSERID_LOGOUT_URL'] = '/userauth/logout'
    browser_id.init_app(app)

# proxy auth

def init_app_proxy(app):
    header = app.config['RELENGAPI_AUTHENTICATION'].get('header', 'REMOTE_USER')

    # request_loader is invoked on every request
    @login_manager.request_loader
    def request_loader(request):
        username = request.headers.get(header)
        if username:
            return User(username)

# views

@bp.route("/account")
@login_required
def account():
    return render_template("account.html")


@bp.route('/login_request')
def login_request():
    if current_user.is_authenticated():
        next = request.args.get('next') or url_for('root')
        return redirect(next)
    return render_template('login_request.html')

# initialization

@bp.record
def init_blueprint(state):
    app = state.app
    init_app_login_manager(app)

    auth_type = app.config.get('RELENGAPI_AUTHENTICATION', {}).get('type', 'browserid')
    # stash this for the template
    app.config['RELENGAPI_AUTHENTICATION_TYPE'] = auth_type

    auth_init = {
        'browserid': init_app_browserid,
        'proxy': init_app_proxy,
    }.get(auth_type, None)
    if not auth_init:
        raise RuntimeError("no such auth type '%s'" % (auth_type,))
    auth_init(app)
