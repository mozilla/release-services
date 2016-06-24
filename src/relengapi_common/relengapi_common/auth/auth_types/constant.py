# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import redirect
from flask import request
from flask import url_for
from flask_login import login_user
from flask_login import logout_user

from relengapi_common import auth
from relengapi_common import utils


def init_app(app):
    config = app.config['RELENGAPI_AUTHENTICATION']

    # steal the JS from auth_external, since this is very similar
    # TODO: we need to package this with webpack
    #app.layout.add_script("/static/js/auth_external.js")

    @app.route('/userauth/login')
    def login():
        login_user(auth.HumanUser(config['email']))
        return _finish_request()

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
        return redirect(utils.safe_redirect_path(next_url))
