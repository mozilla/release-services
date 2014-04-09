# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import render_template
from flask import flash
from flask.ext.principal import identity_changed, Identity
from flask.ext.browserid import BrowserID
from .user import User

class BrowserIDAuth(object):

    def __init__(self, app):
        browser_id = BrowserID()

        @browser_id.user_loader
        def browser_id_user_loader(login_info):
            if login_info['status'] != 'okay':
                return None
            identity_changed.send(app, identity=Identity(login_info['email']))
            flash("Authenticated as %s" % login_info['email'], 'success')
            return User(login_info['email'])

        # TODO: call identity_changed on logout, too

        # this really shouldn't be app config, but whatever
        app.config['BROWSERID_LOGIN_URL'] = '/userauth/login'
        app.config['BROWSERID_LOGOUT_URL'] = '/userauth/logout'
        browser_id.init_app(app)

    def login_request(self):
        return render_template('browserid_login_prompt.html')
