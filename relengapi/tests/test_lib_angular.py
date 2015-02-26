# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import url_for
from nose.tools import assert_raises
from relengapi.lib import angular
from relengapi.lib.testing.context import TestContext

test_context = TestContext(reuse_app=False)


@test_context
def test_template_success(app):
    with app.test_request_context('/'):
        res = angular.template('testtpl.html',
                               url_for('static', filename='js/relengapi.js'))
        assert 'Test template' in res, res


@test_context
def test_template_bad_dep_url(app):
    with app.test_request_context('/'):
        assert_raises(RuntimeError, lambda:
                      angular.template('testtpl.html',
                                       url_for('static', filename='background.jpg')))


@test_context
def test_template_no_static_folder(app):
    # fake not having a static folder
    with app.test_request_context('/'):
        app.static_folder = None
        assert_raises(RuntimeError, lambda:
                      angular.template('testtpl.html'))
