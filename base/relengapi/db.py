# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa
from flask import current_app
from sqlalchemy import orm
from sqlalchemy.orm import scoping
from sqlalchemy.ext import declarative


class _QueryProperty(object):

    def __init__(self, dbname):
        self.dbname = dbname

    def __get__(self, obj, cls):
        return current_app.db.session[self.dbname].query(cls)


_declarative_bases = {}


def declarative_base(dbname):
    try:
        return _declarative_bases[dbname]
    except KeyError:
        _declarative_bases[dbname] = b = declarative.declarative_base()
        b.query = _QueryProperty(dbname)
        return b


class Alchemies(object):

    """
    A container that handles access to SQLALchemy metadata and connection
    pools.  This is available in requests at g.db, or as current_app.db.
    """

    def __init__(self, app):
        self.app = app
        self._engines = {}

        # set up a session for each db, using scoped_session (based on the
        # thread ID)
        self.session = {}
        for dbname in self.database_names:
            Session = orm.sessionmaker(bind=self.engine(dbname))
            self.session[dbname] = scoping.scoped_session(Session)

    def engine(self, dbname):
        # lazily set up engines
        if dbname not in self._engines:
            uri = self.app.config['SQLALCHEMY_DATABASE_URIS'][dbname]
            self._engines[dbname] = sa.create_engine(uri)
        return self._engines[dbname]

    @property
    def database_names(self):
        return _declarative_bases.keys()

    @property
    def metadata(self):
        return dict((k, v.metadata) for k, v in _declarative_bases.iteritems())


def make_db(app):
    return Alchemies(app)
