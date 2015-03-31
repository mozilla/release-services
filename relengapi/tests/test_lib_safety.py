# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib import safety
from relengapi.lib.testing.context import TestContext

testcontext = TestContext(reuse_app=True)


def test_safe_redirect_path_unqualified():
    """A redirect to an unqualified path is alloewd"""
    eq_(safety.safe_redirect_path('/foo/bar'), '/foo/bar')


@testcontext
def test_safe_redirect_path_schema_rejected(app):
    """A redirect to a URL with a schema is not allowed and defaults to root"""
    with app.test_request_context():
        eq_(safety.safe_redirect_path('file:///foo/bar'), '/')


@testcontext
def test_safe_redirect_path_netloc_rejected(app):
    """A redirect to a URL with a netloc is not allowed and defaults to root"""
    with app.test_request_context():
        eq_(safety.safe_redirect_path('//myserver.com/foo/bar'), '/')
