# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from flask import abort
from flask import redirect
from flask import request
from flask import url_for
from flask.ext.login import login_user
from flask.ext.login import logout_user
from relengapi.lib import auth
from relengapi.lib import safety

logger = logging.getLogger(__name__)


def init_app(app):
    config = app.config['RELENGAPI_AUTHENTICATION']

    app.layout.add_script("/static/js/auth_external.js")

    @app.route('/userauth/login')
    def login():
        """/userauth/login view; the frontend should apply its auth to this request
        and identify the user for us"""
        if 'environ' in config:
            environ_key = config['environ']
            email = request.environ.get(environ_key)
        else:
            header = config.get('header', 'REMOTE_USER')
            email = request.headers.get(header)
        if email:
            login_user(auth.HumanUser(email))
            return _finish_request()
        else:
            logger.warning("External authentication data for RELENGAPI_AUTHENTICATION not found")
            abort(500)

    @app.route('/userauth/logout')
    def logout():
        """/userauth/logout view"""
        logout_user()
        return _finish_request()

    def _finish_request():
        if request.args.get('ajax'):
            return 'ok'
        # this was from the browser, so send them somewhere useful
        next_url = request.args.get('next') or url_for('root')
        return redirect(safety.safe_redirect_path(next_url))
