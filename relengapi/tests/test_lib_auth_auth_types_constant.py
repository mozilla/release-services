# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.login import current_user
from nose.tools import eq_
from relengapi.lib.testing.context import TestContext


test_context = TestContext(
    config={'RELENGAPI_AUTHENTICATION': {'type': 'constant', 'email': 'me@me.com'}})


@test_context
def test_constant_login_logout(app, client):
    @app.route('/username')
    def username():
        return str(current_user)

    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "anonymous:"))
    rv = client.get(
        "/userauth/login?next=%2Fusername")
    eq_((rv.status_code, rv.headers['Location']), (
        302, "http://localhost/username"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "human:me@me.com"))
    rv = client.get("/userauth/logout")
    eq_((rv.status_code, rv.headers['Location']), (302, "http://localhost/"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "anonymous:"))


@test_context
def test_constant_login_ajax(app, client):
    rv = client.get("/userauth/login?ajax=1")
    eq_((rv.status_code, rv.data), (200, 'ok'))
