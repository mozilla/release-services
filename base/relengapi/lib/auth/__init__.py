# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pkg_resources
from flask import flash
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from flask.ext.login import current_user
from flask.ext.login import user_logged_in
from flask.ext.login import user_logged_out
from flask.ext.login import LoginManager


class BaseUser(object):

    anonymous = False
    type = None

    def is_authenticated(self):
        return not self.anonymous

    def is_active(self):
        return not self.anonymous

    def is_anonymous(self):
        return self.anonymous

    @property
    def permissions(self):
        return self.get_permissions()

    def get_permissions(self):
        return []

    def get_id(self):
        raise NotImplementedError

    def __str__(self):
        return self.get_id()


class AnonymousUser(BaseUser):

    anonymous = True
    type = 'anonymous'

    def get_id(self):
        return 'anonymous:'


class HumanUser(BaseUser):

    type = 'human'

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return 'human:%s' % self.authenticated_email


_request_loaders = []


def request_loader(func):
    """
    This registers a callback for loading users based on a Flask request.
    This can be used to support various token authentication schemes.
    """
    _request_loaders.append(func)

# DOC: call flask.ext.login.log{in,out}_user

login_manager = LoginManager()
login_manager.login_view = 'login_request'
login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def _user_loader(session_identifier):
    try:
        typ, email = session_identifier.split(':', 1)
    except ValueError:
        return
    if typ == 'human':
        return HumanUser(email)


@login_manager.request_loader
def _request_loader(request):
    for loader in _request_loaders:
        u = loader(request)
        if u:
            return u


def login_request():
    """Redirect here to ask the user to authenticate"""
    if current_user.is_authenticated():
        next_url = request.args.get('next') or url_for('root')
        return redirect(next_url)
    return render_template("login_request.html")


def logged_in(sender, user):
    flash("Logged in as %s" % user.authenticated_email, 'success')


def logged_out(sender, user):
    flash("Logged out")


def init_app(app):
    login_manager.init_app(app)

    # provide a landing page that asks the user to login
    app.route('/login_request')(login_request)

    # flash notify on login and logout
    user_logged_in.connect(logged_in, app)
    # see https://github.com/maxcountryman/flask-login/issues/162
    user_logged_out.connect(logged_out, app)

    auth_type = app.config.get(
        'RELENGAPI_AUTHENTICATION', {}).get('type', 'browserid')
    app.config['RELENGAPI_AUTHENTICATION_TYPE'] = auth_type

    # load and initialize the appropriate mechanism.  Using entry_points like this
    # avoids even importing plugins this app isn't using
    entry_points = list(
        pkg_resources.iter_entry_points('relengapi.auth.mechanisms', auth_type))
    if len(entry_points) == 0:
        raise RuntimeError("no such authentication type %r" % (auth_type,))
    elif len(entry_points) > 1:
        raise RuntimeError(
            "multiple authentication plugins defined for type %r" % (auth_type,))
    ep = entry_points[0]
    plugin_init_app = ep.load()
    plugin_init_app(app)
