# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import werkzeug
from nose.tools import assert_raises
from nose.tools import eq_
from werkzeug.exceptions import BadRequest

from relengapi.lib import api
from relengapi.lib import http
from relengapi.lib.testing.context import TestContext

test_context = TestContext()


@test_context
def test_response_headers_response(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return werkzeug.Response("Hello, world")
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_response_headers_tuple(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world", 201
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_response_headers_string(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world"
    eq_(client.get('/test').headers['foo'], 'bar')


@test_context
def test_response_headers_error_response(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        return "Hello, world", 400
    assert 'foo' in client.get('/test').headers


@test_context
def test_response_headers_error_raised(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'))
    def response_view_func():
        raise BadRequest("oh noes")
    assert 'foo' in client.get('/test').headers


@test_context
def test_response_headers_error_raised_ignored(app, client):
    @app.route('/test')
    @http.response_headers(('foo', 'bar'), status_codes='2xx')
    def response_view_func():
        raise BadRequest("oh noes")
    assert 'foo' not in client.get('/test').headers


def _add_numeric_route(app, status_codes):
    @app.route('/test/<int:c>')
    @http.response_headers(('foo', 'bar'), status_codes=status_codes)
    def view(c):
        return 'RESPONSE', c


@test_context
def test_response_headers_status_codes_func(app, client):
    """response_headers(.., status_codes=lambda..) attaches headers only to
    responses for which the lambda returns True"""
    _add_numeric_route(app, status_codes=lambda c: c == 201)
    assert 'foo' not in client.get('/test/200').headers
    assert 'foo' in client.get('/test/201').headers


@test_context
def test_response_headers_status_codes_range(app, client):
    """response_headers(.., status_codes='3xx') attaches headers only to
    responses in the 300's"""
    _add_numeric_route(app, status_codes='3xx')
    assert 'foo' not in client.get('/test/400').headers
    assert 'foo' in client.get('/test/303').headers


@test_context
def test_response_headers_status_codes_str():
    """response_headers(.., status_codes='300') raises ValueError"""
    assert_raises(ValueError, lambda:
                  http.response_headers(('foo', 'bar'), status_codes='300'))


@test_context
def test_response_headers_status_codes_int(app, client):
    """response_headers(.., status_codes=302) attaches headers only to
    responses with code 302"""
    _add_numeric_route(app, status_codes=303)
    assert 'foo' not in client.get('/test/302').headers
    assert 'foo' in client.get('/test/303').headers


@test_context
def test_response_headers_status_codes_iterable(app, client):
    """response_headers(.., status_codes=[..]) attaches headers only to
    responses listed in the iterable"""
    _add_numeric_route(app, status_codes=[401, 404])
    assert 'foo' not in client.get('/test/400').headers
    assert 'foo' in client.get('/test/401').headers
    assert 'foo' not in client.get('/test/4u3').headers


@test_context
def test_response_headers_api_get_data(app, client):
    """View functions decorated with response_headers can still be
    used in api.get_data calls"""
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
