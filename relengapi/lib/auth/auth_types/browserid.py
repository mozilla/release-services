# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.browserid import BrowserID
from relengapi.lib import auth


browser_id = BrowserID()


@browser_id.user_loader
def browser_id_user_loader(login_info):
    if login_info['status'] != 'okay':
        return None
    return auth.HumanUser(login_info['email'])


def init_app(app):
    app.layout.add_script("https://login.persona.org/include.js")
    app.layout.add_script("/static/js/browserid.js")

    # this really shouldn't be app config, but that's how the browserid
    # extension works..
    app.config['BROWSERID_LOGIN_URL'] = '/userauth/login'
    app.config['BROWSERID_LOGOUT_URL'] = '/userauth/logout'
    browser_id.init_app(app)
