# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os.path
import shutil
import tempfile

from flask import url_for
from relengapi.lib import angular
from relengapi.lib.testing.context import TestContext


tempdir = None


def setup_module():
    global tempdir
    tempdir = tempfile.mkdtemp()
    open(os.path.join(tempdir, "test_angular.html"), "w").write(
        'angular-template-content')


def teardown_module():
    shutil.rmtree(tempdir)


def app_setup(app):
    app.static_folder = tempdir

    @app.route('/angular_template')
    def angular_template():
        return angular.template('test_angular.html',
                                url_for('static', filename='test_angular.js'),
                                url_for('static', filename='test_angular.css'),
                                data=['some', 'data'])

test_context = TestContext(app_setup=app_setup, reuse_app=True)


@test_context
def test_render_template(client):
    rendered = client.get('/angular_template').data
    # initial data is included
    assert '["some", "data"]' in rendered, rendered
    # template content is included
    assert 'angular-template-content' in rendered, rendered
    # js dependencies
    assert '<script src="/static/test_angular.js" type="text/javascript"></script>' \
        in rendered, rendered
    # css dependencies
    assert '<link href="/static/test_angular.css" media="screen"' \
        in rendered, rendered
    # user type
    assert '"type": "anonymous"' in rendered, rendered
