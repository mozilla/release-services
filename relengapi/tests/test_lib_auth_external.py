# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask.ext.login import current_user
from nose.tools import eq_
from relengapi.lib.testing.context import TestContext


test_context = TestContext(
    config={'RELENGAPI_AUTHENTICATION': {'type': 'external', 'environ': 'TEST'}})


@test_context
def test_external_login_logout(app, client):
    @app.route('/username')
    def username():
        return str(current_user)

    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "anonymous:"))
    rv = client.get(
        "/userauth/login?next=%2Fusername", environ_overrides={'TEST': 'jimmy'})
    eq_((rv.status_code, rv.headers['Location']), (
        302, "http://localhost/username"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "human:jimmy"))
    rv = client.get("/userauth/logout")
    eq_((rv.status_code, rv.headers['Location']), (302, "http://localhost/"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "anonymous:"))
