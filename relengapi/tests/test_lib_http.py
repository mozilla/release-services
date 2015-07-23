# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import werkzeug

from nose.tools import eq_

from relengapi.lib import api
from relengapi.lib import http
from relengapi.lib.testing.context import TestContext

test_context = TestContext()


@test_context
def test_response(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return werkzeug.Response("Hello, world")
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_tuple(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world", 201
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_string(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world"
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_error(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world", 400
    assert 'foo' not in client.get('/test').headers


@test_context
def test_api_get_data(app, client):
    @app.route('/test/api')
    @http.response_headers(('foo', 'bar'))
    @api.apimethod([unicode])
    def api_func():
        return ['a', 'b']

    @app.route('/test')
    def view_func():
        api.get_data(api_func)
        return "OK"
    resp = client.get('/test')
    eq_(resp.status_code, 200)
