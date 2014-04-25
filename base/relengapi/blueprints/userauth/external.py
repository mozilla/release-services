# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from flask import abort
from flask import url_for
from flask import flash
from flask import redirect
from flask import request
from flask import current_app
from flask.ext.login import login_user, logout_user
from flask.ext.principal import identity_changed, Identity, AnonymousIdentity
from .user import User

logger = logging.getLogger(__name__)

class ExternalAuth(object):

    def __init__(self, app):
        config = app.config['RELENGAPI_AUTHENTICATION']
        if 'environ' in config:
            environ_key = config['environ']
            self.user_getter = lambda request: request.environ.get(environ_key)
        else:
            header = config.get('header', 'REMOTE_USER')
            self.user_getter = lambda request: request.headers.get(header)

        app.route('/userauth/login')(self.login)
        app.route('/userauth/logout')(self.logout)

    def login_request(self):
        # users are redirected here to login; redirect to the login link to get
        # external auth, carrying along any next URL
        next = request.args.get('next') or url_for('root')
        return redirect(url_for('login', next=next))

    def login(self):
        """/userauth/login view; the frontend should apply its auth to this request
        and identify the user for us"""
        username = self.user_getter(request)
        if username:
            login_user(User(username))
            identity_changed.send(current_app, identity=Identity(username, 'user'))
            flash("Authenticated as %s" % username, 'success')
            return self._finish_request()
        else:
            logger.warning("External authentication data for RELENGAPI_AUTHENTICATION not found")
            abort(500)

    def logout(self):
        """/userauth/logout view"""
        logout_user()
        identity_changed.send(current_app, identity=AnonymousIdentity())
        return self._finish_request()

    def _finish_request(self):
        if request.args.get('ajax'):
            return 'ok'
        # this was from the browser, so send them somewhere useful
        next = request.args.get('next') or url_for('root')
        return redirect(next)
