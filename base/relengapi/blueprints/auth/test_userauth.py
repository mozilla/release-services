# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from flask.ext.login import current_user
from relengapi.testing import TestContext


browserid_test_context = TestContext(
        config={'RELENGAPI_AUTHENTICATION': {'type': 'browserid'}})


@browserid_test_context
def test_browserid_login(app, client):
    # all of the fun bits of browserid are in the extension, which has its own
    # tests.  This just verifies that the auth type loads and can handle a request.
    client.get('/userauth/login_request')

external_environ_test_context = TestContext(
        config={'RELENGAPI_AUTHENTICATION': {'type': 'external', 'environ': 'TEST'}})


@external_environ_test_context
def test_external_login_request_redirect(app, client):
    rv = client.get('/userauth/login_request?next=%2Fusername')
    eq_((rv.status_code, rv.headers['Location']),
        (302, "http://localhost/userauth/login?next=%2Fusername"))


@external_environ_test_context
def test_external_login_logout(app, client):
    @app.route('/username')
    def username():
        if current_user.is_authenticated():
            return current_user.authenticated_email
        else:
            return 'no user'

    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "no user"))
    rv = client.get("/userauth/login?next=%2Fusername", environ_overrides={'TEST': 'jimmy'})
    eq_((rv.status_code, rv.headers['Location']), (302, "http://localhost/username"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "jimmy"))
    rv = client.get("/userauth/logout")
    eq_((rv.status_code, rv.headers['Location']), (302, "http://localhost/"))
    rv = client.get("/username")
    eq_((rv.status_code, rv.data), (200, "no user"))
