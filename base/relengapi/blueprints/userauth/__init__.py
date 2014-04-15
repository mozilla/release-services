# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import current_app
from flask.ext.login import login_required
from flask.ext.login import current_user
from flask.ext.login import LoginManager
from flask.ext.principal import Principal
from .user import User


bp = Blueprint('userauth', __name__, template_folder='templates')
login_manager = LoginManager()


def init_app_login_manager(app):
    @login_manager.user_loader
    def login_manager_user_loader(authenticated_email):
        return User(authenticated_email)

    # configure the login manager to redirect to a bare "please login" page when
    # a login is required
    login_manager.login_view = 'userauth.login_request'
    login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
    login_manager.init_app(app)


def init_app_principal(app):
    Principal(app, use_sessions=True)


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
    return current_app.auth.login_request()

def make_support_class(app, mechanisms, config_key, default):
    mechanism = app.config.get(config_key, {}).get('type', default)
    try:
        module_name, class_name = mechanisms[mechanism]
    except KeyError:
        raise RuntimeError("no such %s type '%s'" % (config_key, mechanism))

    # stash this for easy access from the templates
    app.config[config_key + '_TYPE'] = mechanism

    mech_module = importlib.import_module(module_name, __name__)
    mech_class = getattr(mech_module, class_name)
    return mech_class(app)


@bp.record
def init_blueprint(state):
    app = state.app
    init_app_login_manager(app)
    init_app_principal(app)

    auth_mechanisms = {
        'browserid': ('.browserid', 'BrowserIDAuth'),
        'external': ('.external', 'ExternalAuth'),
    }
    app.auth = make_support_class(app, auth_mechanisms,
                                  'RELENGAPI_AUTHENTICATION',
                                  'browserid')
    action_mechanisms = {
        'static': ('.static_actions', 'StaticActions'),
    }
    app.actions = make_support_class(app, action_mechanisms,
                                   'RELENGAPI_ACTIONS',
                                   'static')
