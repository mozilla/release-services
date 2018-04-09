# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib

import connexion
import flask
import werkzeug

import cli_common.log

logger = cli_common.log.get_logger(__name__)


def common_error_handler(exception):
    '''TODO: add description

    :param extension:  TODO
    :type exception: Exception

    :rtype: TODO:
    '''

    if not isinstance(exception, werkzeug.exceptions.HTTPException):
        exception = werkzeug.exceptions.InternalServerError()

    return connexion.problem(
        title=exception.name,
        detail=exception.description,
        status=exception.code,
    )


class Api:
    '''TODO: add description
       TODO: annotate class
    '''

    def __init__(self, app):
        '''
        TODO: add description
        TODO: annotate function
        '''
        self.__app = app

        logger.debug('Setting JSON encoder.')

        app.json_encoder = connexion.apps.flask_app.FlaskJSONEncoder

        logger.debug('Setting common error handler for all error codes.')
        for error_code in werkzeug.exceptions.default_exceptions:
            app.register_error_handler(error_code, common_error_handler)

    def register(self,
                 swagger_file,
                 base_path=None,
                 arguments=None,
                 auth_all_paths=False,
                 swagger_json=True,
                 swagger_ui=True,
                 swagger_path=None,
                 swagger_url='docs',
                 validate_responses=True,
                 strict_validation=True,
                 resolver=connexion.resolver.Resolver(),
                 ):
        '''Adds an API to the application based on a swagger file

        :param swagger_file: swagger file with the specification
        :type swagger_file: str

        :param base_path: base path where to add this api
        :type base_path: str | None

        :param arguments: api version specific arguments to replace on the
                          specification
        :type arguments: dict | None

        :param auth_all_paths: whether to authenticate not defined paths
        :type auth_all_paths: bool

        :param swagger_json: whether to include swagger json or not
        :type swagger_json: bool

        :param swagger_ui: whether to include swagger ui or not
        :type swagger_ui: bool

        :param swagger_path: path to swagger-ui directory
        :type swagger_path: string | None

        :param swagger_url: URL to access swagger-ui documentation
        :type swagger_url: string | None

        :param validate_responses: True enables validation. Validation errors
                                   generate HTTP 500 responses.
        :type validate_responses: bool

        :param strict_validation: True enables validation on invalid request
                                  parameters
        :type strict_validation: bool

        :param resolver: Operation resolver.
        :type resolver: connexion.resolver.Resolver | types.FunctionType

        :rtype: None
        '''

        app = self.__app
        if hasattr(resolver, '__call__'):
            resolver = connexion.resolver.Resolver(resolver)

        logger.debug('Adding API: %s', swagger_file)

        self.swagger_url = swagger_url
        self.__api = connexion.apis.flask_api.FlaskApi(
            specification=pathlib.Path(swagger_file),
            base_path=base_path,
            arguments=arguments,
            swagger_json=swagger_json,
            swagger_ui=swagger_ui,
            swagger_path=swagger_path,
            swagger_url=swagger_url,
            resolver=resolver,
            validate_responses=validate_responses,
            strict_validation=strict_validation,
            auth_all_paths=auth_all_paths,
            debug=app.debug,
        )
        app.register_blueprint(self.__api.blueprint)

        for code, exception in werkzeug.exceptions.default_exceptions.items():
            app.register_error_handler(exception, handle_default_exceptions)

        return self.__api


def handle_default_exceptions(e):
    return flask.jsonify({
        'type': 'about:blank',
        'title': str(e),
        'status': e.code,
        'detail': e.description,
        'instance': 'about:blank',
    }), e.code


def init_app(app):
    return Api(app)
