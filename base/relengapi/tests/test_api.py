# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import mock
from nose.tools import eq_
from flask import Response
from relengapi.lib import api
from relengapi import testing
from werkzeug.exceptions import BadRequest


def app_setup(app):
    @app.route('/apimethod/ok')
    @api.apimethod()
    def ok():
        return ['ok']

    @app.route('/apimethod/fail')
    @api.apimethod()
    def fail():
        raise BadRequest

    @app.route('/apimethod/201')
    @api.apimethod()
    def ok_201():
        return ['ok'], 201

    @app.route('/apimethod/201/header')
    @api.apimethod()
    def ok_201_header():
        return ['ok'], 201, {'X-Header': 'Header'}

    @app.route('/apimethod/header')
    @api.apimethod()
    def ok_header():
        return ['ok'], {'X-Header': 'Header'}


test_context = testing.TestContext(app_setup=app_setup, reuse_app=True)


def test_get_handler():
    @mock.patch('relengapi.util.is_browser')
    def t(util_is_browser, is_browser, expected):
        util_is_browser.return_value = is_browser
        eq_(str(api._get_handler().media_type), expected)

    yield lambda: t(is_browser=True, expected='text/html')
    yield lambda: t(is_browser=False, expected='application/json')


@test_context
def test_JsonHandler_render_response(app):
    h = api.JsonHandler()
    with app.test_request_context():
        eq_(json.loads(h.render_response([1, 2, 3]).data),
            {'result': [1, 2, 3]})


@test_context
def test_HtmlHandler_render_response(app):
    h = api.HtmlHandler()
    with app.test_request_context():
        resp = Response(h.render_response([1, 2, 3]))
        assert '<html' in resp.data, resp.data
        assert "1," in resp.data, resp.data


def test_apimethod():
    @test_context
    def t(client, path, exp_status_code=200, exp_data=None, exp_headers=None):
        resp = client.get(path)
        eq_(resp.status_code, exp_status_code)
        eq_(json.loads(resp.data), exp_data or {'result': ['ok']})
        for k, v in (exp_headers or {}).iteritems():
            assert resp.headers[k] == v

    yield lambda: t(path='/apimethod/ok')
    yield lambda: t(path='/apimethod/fail', exp_status_code=400,
                    exp_data={'error': {
                        'code': 400,
                        'description': '<p>The browser (or proxy) sent a request that this '
                        'server could not understand.</p>',
                        'name': 'Bad Request',
                    }})
    yield lambda: t(path='/apimethod/201', exp_status_code=201)
    yield lambda: t(path='/apimethod/201/header', exp_status_code=201,
                    exp_headers={'X-Header': 'Header'})
    yield lambda: t(path='/apimethod/header', exp_headers={'X-Header': 'Header'})
