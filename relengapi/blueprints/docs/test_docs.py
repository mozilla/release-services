# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock
import os
import shutil
import sys

from nose.tools import eq_
from relengapi.blueprints import docs
from relengapi.lib.testing.context import TestContext
from sphinx import websupport


class NullStorage(websupport.StorageBackend):
    pass

temp_root = os.path.join(os.path.dirname(__file__), 'temp')


def app_setup(app):
    # build the docs somewhere unrelated to the user's builddir
    builddir = os.path.join(temp_root, 'build')
    os.makedirs(builddir)
    app.config['DOCS_BUILD_DIR'] = builddir
    if hasattr(app, 'docs_websupport'):
        del app.docs_websupport

    # delete the srcdir, since we're running in development mode
    srcdir = os.path.join(sys.prefix, 'relengapi-docs')
    if os.path.exists(srcdir):
        shutil.rmtree(srcdir)

    with app.app_context():
        args = mock.Mock()
        args.quiet = True
        args.development = True
        docs.BuildDocsSubcommand().run(mock.Mock, args)

test_context = TestContext(app_setup=app_setup, reuse_app=True)


def teardown_module():
    # clean up the built docs
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)


@test_context
def test_doc(client):
    resp = client.get('/docs/')
    eq_(resp.status_code, 200, resp.data)
    assert 'Development' in resp.data, resp.data

    resp = client.get('/docs/deployment/')
    eq_(resp.status_code, 200, resp.data)
    assert 'Deployment' in resp.data, resp.data

    resp = client.get('/docs/no-such-thing/')
    eq_(resp.status_code, 404, resp.data)


@test_context
def test_static(client):
    resp = client.get('/docs/static/_static/websupport-custom.css')
    eq_(resp.status_code, 200, resp.data)
    assert 'a copy of the MPL' in resp.data, resp.data
