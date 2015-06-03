# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import signals
from flask import url_for
from flask.ext.login import LoginManager
from flask.ext.login import current_user
from flask.ext.login import user_logged_in
from flask.ext.login import user_logged_out
from relengapi.lib import safety
from relengapi.lib.permissions import p


class BaseUser(object):

    anonymous = False
    type = None

    def __eq__(self, other):
        return isinstance(other, BaseUser) and self.get_id() == other.get_id()

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
        return set()

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
        self._permissions = None

    def get_id(self):
        return 'human:%s' % self.authenticated_email

    def get_permissions(self):
        if self._permissions is not None:
            return self._permissions
        if 'perms' in session and session.get('perms_exp', 0) > time.time():
            self._permissions = set(p[perm] for perm in session['perms'])
        else:
            self._permissions = perms = set()
            permissions_stale.send(
                current_app._get_current_object(), user=self, permissions=perms)
            session['perms'] = [str(perm) for perm in perms]
            lifetime = current_app.config.get(
                'RELENGAPI_PERMISSIONS', {}).get('lifetime', 3600)
            session['perms_exp'] = int(time.time() + lifetime)
        return self._permissions


_request_loaders = []


def request_loader(func):
    """
    This registers a callback for loading users based on a Flask request.
    This can be used to support various token authentication schemes.
    """
    _request_loaders.append(func)

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
            if not isinstance(u.permissions, set):
                raise TypeError("user permissions must be a set")
            return u


def login_request():
    """Redirect here to ask the user to authenticate"""
    if current_user.is_authenticated():
        next_url = request.args.get('next') or url_for('root')
        return redirect(safety.safe_redirect_path(next_url))
    return render_template("login_request.html")


def _clear_perms_cache():
    for k in 'perms', 'perms_exp':
        if k in session:
            del session[k]


def logged_in(sender, user):
    _clear_perms_cache()
    flash("Logged in as %s" % user.authenticated_email, 'success')


def logged_out(sender, user):
    _clear_perms_cache()
    flash("Logged out")


def _init_mod(app, var_name, default, root_package):
    mod_name = app.config.get(var_name, {}).get('type', default)
    app.config[var_name + '_TYPE'] = mod_name
    mod_name = mod_name.replace('-', '_')
    mod_path = root_package + '.' + mod_name
    try:
        mod = __import__(mod_path)
    except ImportError:
        raise RuntimeError("no such %s %r" % (var_name, mod_name,))
    for atom in mod_path.split('.')[1:]:
        mod = getattr(mod, atom)
    mod.init_app(app)


def init_app(app):
    login_manager.init_app(app)

    # provide a landing page that asks the user to login
    app.route('/login_request')(login_request)

    # flash notify on login and logout
    user_logged_in.connect(logged_in, app)
    # see https://github.com/maxcountryman/flask-login/issues/162
    user_logged_out.connect(logged_out, app)

    _init_mod(app, 'RELENGAPI_AUTHENTICATION', 'browserid', 'relengapi.lib.auth.auth_types')
    _init_mod(app, 'RELENGAPI_PERMISSIONS', 'static', 'relengapi.lib.auth.perms_types')

permissions_stale = signals.Namespace().signal('permissions_stale')
