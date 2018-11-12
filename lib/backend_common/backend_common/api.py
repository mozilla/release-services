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
                 specification,
                 base_path=None,
                 arguments=None,
                 validate_responses=True,
                 strict_validation=True,
                 resolver=None,
                 auth_all_paths=False,
                 debug=False,
                 resolver_error_handler=None,
                 validator_map=None,
                 pythonic_params=False,
                 pass_context_arg_name=None,
                 options=None
                 ):
        '''Adds an API to the application based on a swagger file
        '''

        app = self.__app

        logger.debug('Adding API: {}'.format(specification))

        self.__api = api = connexion.apis.flask_api.FlaskApi(
            specification=pathlib.Path(specification),
            base_path=base_path,
            arguments=arguments,
            validate_responses=validate_responses,
            strict_validation=strict_validation,
            resolver=resolver,
            auth_all_paths=auth_all_paths,
            debug=app.debug,
            resolver_error_handler=resolver_error_handler,
            validator_map=validator_map,
            pythonic_params=pythonic_params,
            pass_context_arg_name=pass_context_arg_name,
            options=options,
        )
        self.swagger_url = api.options.openapi_console_ui_path
        app.register_blueprint(api.blueprint)

        for code, exception in werkzeug.exceptions.default_exceptions.items():
            app.register_error_handler(exception, handle_default_exceptions)

        return api


def handle_default_exceptions_raw(e):
    code = getattr(e, 'code', 500)
    description = getattr(e, 'description', str(e))
    return {
        'type': 'about:blank',
        'title': str(e),
        'status': code,
        'detail': description,
        'instance': 'about:blank',
    }


def handle_default_exceptions(e):
    error = handle_default_exceptions_raw(e)
    return flask.jsonify(error), error['status']


def init_app(app):
    return Api(app)


def app_heartbeat():
    pass
