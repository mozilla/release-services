# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import relengapi.app
from nose.tools import make_decorator


class TestContext(object):

    def __init__(self, databases=[], db_setup=None,
                 db_teardown=None, reuse_app=False):
        self.databases = set(databases)
        if db_setup:
            self.db_setup = db_setup
        if db_teardown:
            self.db_teardown = db_teardown
        self.reuse_app = reuse_app
        self._app = None

    def db_setup(self, app):
        pass

    def db_teardown(self, app):
        pass

    def _make_app(self):
        if self.reuse_app and self._app:
            return self._app
        config = {}
        config['TESTING'] = True
        config['SECRET_KEY'] = 'test'
        config['SQLALCHEMY_DATABASE_URIS'] = uris = {}
        for dbname in self.databases:
            uris[dbname] = 'sqlite://'
        app = relengapi.app.create_app(test_config=config)

        # set up the requested DBs
        for dbname in self.databases:
            meta = app.db.metadata[dbname]
            engine = app.db.engine(dbname)
            meta.create_all(bind=engine)
        self._app = app
        return app

    def __call__(self, func):
        arginfo = inspect.getargspec(func)
        args = set((arginfo.args if arginfo.args else []) +
                   (arginfo.keywords if arginfo.keywords else []))

        @make_decorator(func)
        def wrap():
            kwargs = {}
            app = self._make_app()
            if 'app' in args:
                kwargs['app'] = app
            if 'client' in args:
                kwargs['client'] = app.test_client()
            self.db_setup(app)
            try:
                func(**kwargs)
            finally:
                self.db_teardown(app)
        return wrap
