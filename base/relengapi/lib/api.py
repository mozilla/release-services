# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import traceback
import sys
from flask import json
from flask import jsonify
from flask import render_template
from flask import request
from flask import current_app
from relengapi import util
from werkzeug.exceptions import HTTPException
import wrapt


class Handler(object):

    def _parse_result(self, result):
        code = 200
        headers = {}
        if isinstance(result, tuple):
            if len(result) == 2:
                if isinstance(result[1], dict):
                    result, headers = result
                else:
                    result, code = result
            else:
                result, code, headers = result
            assert 200 <= code < 299
        return result, code, headers


class JsonHandler(Handler):
    """Handler for requests accepting application/json."""
    media_type = 'application/json'

    def render_response(self, result):
        result, code, headers = self._parse_result(result)
        resp = jsonify(result=result)
        resp.status_code = code
        resp.headers.extend(headers)
        return resp

    def handle_exception(self, exc_type, exc_value, exc_tb):
        if isinstance(exc_value, HTTPException):
            resp = jsonify(error={
                'code': exc_value.code,
                'name': exc_value.name,
                'description': exc_value.get_description(request),
            })
            resp.status_code = exc_value.code
        else:
            current_app.log_exception((exc_type, exc_value, exc_tb))
            error = {
                'code': 500,
                'name': 'Internal Server Error',
                'description': 'Enable debug mode for more information',
            }
            if current_app.debug:
                error['traceback'] = traceback.format_exc().split('\n')
                error['name'] = exc_type.__name__
                error['description'] = str(exc_value)
            resp = jsonify(error)
            resp.status_code = 500
        return resp


class HtmlHandler(Handler):
    """Handler for requests accepting text/html"""
    media_type = 'text/html'

    def render_response(self, result):
        return render_template('api_json.html', json=json.dumps(dict(result=result), indent=4))

    def handle_exception(self, exc_type, exc_value, exc_tb):
        if isinstance(exc_value, HTTPException):
            return current_app.handle_http_exception(exc_value)
        else:
            raise exc_type, exc_value, exc_tb


def _get_handler():
    """Get an appropriate handler based on the request"""
    return HtmlHandler() if util.is_browser() else JsonHandler()


def init_app(app):
    # install a universal error handler that will render errors based on the
    # Accept header in the request
    @app.errorhandler(Exception)
    def exc_handler(error):
        exc_type, exc_value, tb = sys.exc_info()
        h = _get_handler()
        return h.handle_exception(exc_type, exc_value, tb)

    # always trap http exceptions; the HTML handler will render them
    # as expected, but the JSON handler needs its chance, too
    app.trap_http_exception = lambda e: True


def apimethod():
    @wrapt.decorator
    def wrap(wrapper, instance, args, kwargs):
        h = _get_handler()
        rv = wrapper(*args, **kwargs)
        return h.render_response(rv)
    return wrap
