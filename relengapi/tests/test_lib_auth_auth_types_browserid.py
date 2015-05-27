# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib.auth.auth_types import browserid
from relengapi.lib.testing.context import TestContext


test_context = TestContext(
    config={'RELENGAPI_AUTHENTICATION': {'type': 'browserid'}})


@test_context
def test_browserid_callback(app, client):
    # all of the fun bits of browserid are in the extension, which has its own
    # tests.  This just verifies that the user_loader works.
    cb = browserid.browser_id.login_callback
    eq_(cb({'status': 'bad'}), None)
    eq_(cb({'status': 'okay', 'email': 'jeanne'}).authenticated_email, 'jeanne')
