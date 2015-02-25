# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import sys
import traceback
import werkzeug
import wsme
import wsme.api
import wsme.rest.args
import wsme.rest.json
import wsme.types

from flask import Response
from flask import current_app
from flask import json
from flask import jsonify
from flask import render_template
from flask import request
from relengapi import util
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import HTTPException


class JsonHandler(object):

    """Handler for requests accepting application/json."""
    media_type = 'application/json'

    def render_response(self, result, code, headers):
        resp = jsonify(result=result)
        resp.status_code = code
        resp.headers.extend(headers)
        return resp

    def handle_exception(self, exc_type, exc_value, exc_tb):
        if isinstance(exc_value, HTTPException):
            resp = jsonify(error={
                'code': exc_value.code,
                'name': exc_value.name,
                'description': exc_value.description,
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
            resp = jsonify(error=error)
            resp.status_code = 500
        return resp


class HtmlHandler(object):

    """Handler for requests accepting text/html"""
    media_type = 'text/html'

    def render_response(self, result, code, headers):
        json_ = json.dumps(dict(result=result), indent=4)
        tpl = render_template('api_json.html', json=json_)
        return Response(tpl, code, headers)

    def handle_exception(self, exc_type, exc_value, exc_tb):
        if isinstance(exc_value, HTTPException):
            return current_app.handle_http_exception(exc_value)
        else:
            raise exc_type, exc_value, exc_tb


def _get_handler():
    """Get an appropriate handler based on the request"""
    return HtmlHandler() if util.is_browser() else JsonHandler()


def apimethod(return_type, *arg_types, **options):
    def wrap(wrapped):
        # adapted from wsmeext.flask (MIT-licensed)
        wsme.signature(return_type, *arg_types, **options)(wrapped)
        funcdef = wsme.api.FunctionDefinition.get(wrapped)
        funcdef.resolve_types(wsme.types.registry)

        @functools.wraps(wrapped)
        def replacement(*args, **kwargs):
            data_only = kwargs.pop('_data_only_', False)
            if data_only:
                return wrapped(*args, **kwargs)

            try:
                args, kwargs = wsme.rest.args.get_args(
                    funcdef, args, kwargs,
                    request.args, request.form,
                    request.data, request.mimetype)
            except wsme.exc.ClientSideError as e:
                raise BadRequest(e.faultstring)
            result = wrapped(*args, **kwargs)
            # if this is a Response (e.g., a redirect), just return it
            if isinstance(result, werkzeug.Response):
                return result

            # parse the result, if it was a tuple
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

            # convert the objects into jsonable simple types, also checking
            # the type at the same time
            result = wsme.rest.json.tojson(funcdef.return_type, result)

            # and hand to render_response, which will actually
            # generate the appropriate string form
            h = _get_handler()
            return h.render_response(result, code, headers)
        replacement.__apidoc__ = wrapped.__doc__
        return replacement
    return wrap


def get_data(view_func, *args, **kwargs):
    kwargs['_data_only_'] = True
    # flag this as a subrequest, so that is_browser returns False
    request.is_subrequest = True
    try:
        rv = view_func(*args, **kwargs)
    finally:
        del request.is_subrequest
    if isinstance(rv, werkzeug.Response):
        # this generally indicates that some other decorator decided to handle
        # making the response itself -- at any rate, not what we want!
        raise ValueError("cannot access data required for page")
    return rv


class JsonObject(wsme.types.UserType):

    basetype = dict
    name = 'JsonObject'

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Wrong type. Expected JSON object, got '%s'"
                             % (type(value),))

        # try dumping it to make sure it's JSON-able
        try:
            json.dumps(value)
        except Exception:
            raise ValueError("Cannot be converted to JSON")

        return value

# provide a single instance for use in WSME types
jsonObject = JsonObject()


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

    # create a new subclass of the current json_encoder, that can handle
    # encoding WSME types
    old_json_encoder = app.json_encoder

    class WSMEEncoder(old_json_encoder):

        """A mixin for JSONEncoder which can handle WSME types"""

        def default(self, o):
            if isinstance(o, wsme.types.Base):
                return wsme.rest.json.tojson(type(o), o)
            return old_json_encoder.default(self, o)

    app.json_encoder = WSMEEncoder
