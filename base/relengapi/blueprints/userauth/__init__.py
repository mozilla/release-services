# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import url_for
from flask_login import login_required
from flask_login import current_user
from relengapi import login_manager
from flask.ext.login import UserMixin
from flask.ext.principal import identity_changed, identity_loaded, RoleNeed, Identity, Principal


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

# principal


def init_app_principal(app):
    Principal(app, use_sessions=True)

# browserid auth


def init_app_browserid(app):
    from flask.ext.browserid import BrowserID
    browser_id = BrowserID()

    @browser_id.user_loader
    def browser_id_user_loader(login_info):
        if login_info['status'] != 'okay':
            return None
        identity_changed.send(app, identity=Identity(login_info['email']))
        flash("Authenticated as %s" % login_info['email'])
        return User(login_info['email'])

    # TODO: call identity_changed on logout, too

    # this really shouldn't be app config, but whatever
    app.config['BROWSERID_LOGIN_URL'] = '/userauth/login'
    app.config['BROWSERID_LOGOUT_URL'] = '/userauth/logout'
    browser_id.init_app(app)

# proxy auth


def init_app_proxy(app):
    header = app.config['RELENGAPI_AUTHENTICATION'].get(
        'header', 'REMOTE_USER')

    # request_loader is invoked on every request
    @login_manager.request_loader
    def request_loader(request):
        # TODO: call identity_changed, if it has
        username = request.headers.get(header)
        if username:
            return User(username)

# environ auth


def init_app_environ(app):
    environ_key = app.config['RELENGAPI_AUTHENTICATION'].get(
        'key', 'REMOTE_USER')

    # request_loader is invoked on every request
    @login_manager.request_loader
    def request_loader(request):
        # TODO: call identity_changed, if it has
        username = request.environ.get(environ_key)
        if username:
            return User(username)

# static roles


def init_app_static_roles(app):

    roles_map = app.config.get('RELENGAPI_ROLES', {}).get('roles', {})

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        for role in roles_map.get(identity.id, []):
            identity.provides.add(RoleNeed(role))

# views


@bp.route("/account")
@login_required
def account():
    """Show the user information about their account"""
    return render_template("account.html")


@bp.route('/login_request')
def login_request():
    """Redirect here to ask the user to authenticate"""
    if current_user.is_authenticated():
        next = request.args.get('next') or url_for('root')
        return redirect(next)
    return render_template('login_request.html')

# initialization


@bp.record
def init_blueprint(state):
    app = state.app
    init_app_login_manager(app)
    init_app_principal(app)

    auth_type = app.config.get(
        'RELENGAPI_AUTHENTICATION', {}).get('type', 'browserid')
    auth_init = globals().get('init_app_' + auth_type)
    if not auth_init:
        raise RuntimeError("no such auth type '%s'" % (auth_type,))
    auth_init(app)

    roles_type = app.config.get('RELENGAPI_ROLES', {}).get('type', 'static')
    roles_init = globals().get('init_app_' + roles_type + '_roles')
    if not roles_init:
        raise RuntimeError("no such permission type '%s'" % (roles_type,))
    roles_init(app)

    # stash these for easy access from the templates
    app.config['RELENGAPI_AUTHENTICATION_TYPE'] = auth_type
    app.config['RELENGAPI_ROLES_TYPE'] = roles_type
