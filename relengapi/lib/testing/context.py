# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import logging
import relengapi.app
import wrapt

from flask import json
from relengapi.lib import auth

log = logging.getLogger(__name__)


class TestContext(object):

    _known_options = set([
        'databases',
        'reuse_app',
        'app_setup',
        'db_setup',
        'db_teardown',
        'config',
        'perms',  # TODO: doc
        'user',
        'accept',
    ])

    def __init__(self, **options):
        self._validate(options)
        self.options = options
        self._app = None

    def specialize(self, **options):
        new_options = self.options.copy()
        new_options.update(options)
        return TestContext(**new_options)

    def _validate(self, options):
        unknown = set(options) - self._known_options
        if unknown:
            raise ValueError("unknown options %s" % (', '.join(unknown)))

    def _make_app(self):
        if self.options.get('reuse_app') and self._app:
            return self._app
        config = self.options.get('config', {}).copy()
        config['TESTING'] = True
        config['SECRET_KEY'] = 'test'
        config['SQLALCHEMY_DATABASE_URIS'] = uris = {}
        dbnames = self.options.get('databases', [])
        for dbname in dbnames:
            uris[dbname] = 'sqlite://'
        app = relengapi.app.create_app(test_config=config)

        # translate 'perms' into a logged-in, human user
        user = None
        if 'perms' in self.options:
            perms = self.options.get('perms')
            user = auth.HumanUser('test@test.test')
            user._permissions = perms
        # otherwise, set up logged-in user
        elif 'user' in self.options:
            user = self.options.get('user')

        if user:
            @app.before_request
            def set_user():
                auth.login_manager.reload_user(user)

        # set up the requested DBs
        for dbname in dbnames:
            meta = app.db.metadata[dbname]
            engine = app.db.engine(dbname)
            meta.create_all(bind=engine)
        self._app = app
        if 'app_setup' in self.options:
            self.options['app_setup'](app)
        return app

    def _wrap_client(self, client):
        # create a post_json convenience method
        def post_json(path, data):
            return client.post(
                path, data=json.dumps(data),
                headers=[('Content-Type', 'application/json')])
        client.post_json = post_json

        # patch 'open' to log the request
        old_open = client.open

        def open(path='/', base_url=None, *args, **kwargs):
            method = kwargs.get('method')
            log.info('request: {} {}'.format(method, path))
            resp = old_open(path, base_url, *args, **kwargs)
            log.info('response: {}'.format(resp.status))
            return resp
        client.open = open

    @wrapt.decorator
    def __call__(self, wrapped, instance, given_args, kwargs):
        arginfo = inspect.getargspec(wrapped)
        args = set((arginfo.args if arginfo.args else []) +
                   (arginfo.keywords if arginfo.keywords else []))

        app = self._make_app()
        if 'app' in args:
            kwargs['app'] = app

        if 'client' in args:
            kwargs['client'] = app.test_client()
            self._wrap_client(kwargs['client'])

        if 'db_setup' in self.options:
            self.options['db_setup'](app)
        try:
            wrapped(*given_args, **kwargs)
        finally:
            if 'db_teardown' in self.options:
                self.options['db_teardown'](app)
