# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import flask_oidc


auth0 = flask_oidc.OpenIDConnect()


def init_app(app):
    auth0.init_app(app)
    return auth0
