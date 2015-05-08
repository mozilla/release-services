# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
import os
import pytz
import sqlalchemy as sa
import threading

from flask import current_app
from relengapi.util import synchronized
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy import orm
from sqlalchemy import types
from sqlalchemy.engine import url
from sqlalchemy.ext import declarative
from sqlalchemy.orm import scoping
from sqlalchemy.pool import Pool


logger = logging.getLogger(__name__)


class _QueryProperty(object):

    def __init__(self, dbname):
        self.dbname = dbname

    def __get__(self, obj, cls):
        return current_app.db.session(self.dbname).query(cls)


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
        self._sessions = {}

        # destroy sessions after each Flask request
        @app.teardown_request
        def teardown_request(response_or_exc):
            self.flush_sessions()

    def _get_db_config(self, dbname):
        uris = self.app.config.get('SQLALCHEMY_DATABASE_URIS')
        if uris is not None:
            if dbname not in uris:
                raise KeyError(
                    "No configuration for database '{}'".format(dbname))
            return uris[dbname]
        else:
            # apply a universal default for all databases; this isn't the
            # optimal location, but works well for the developer who just
            # cloned the app and is running it for the first time.
            dir = os.path.join(os.path.dirname(__file__), '../..')
            dir = os.path.abspath(dir)
            uri = 'sqlite:///{}'.format(
                os.path.join(dir, '{}.db'.format(dbname)))
            logger.warning("Using URI {} for database {}".format(uri, dbname))
            return uri

    @synchronized(threading.Lock())
    def engine(self, dbname):
        # Set the log level for db logs
        sqla_logger = logging.getLogger('sqlalchemy.engine')
        if self.app.config.get('SQLALCHEMY_DB_LOG', False):
            sqla_logger.setLevel(logging.INFO)
        else:
            sqla_logger.setLevel(logging.WARNING)

        if dbname not in self._engines:
            uri = self._get_db_config(dbname)
            u = url.make_url(uri)
            dialect = u.drivername.split('+')[0]

            try:
                create_engine = getattr(self, 'create_{}_engine'.format(dialect))
            except AttributeError:
                create_engine = self.create_generic_engine

            self._engines[dbname] = create_engine(u)
        return self._engines[dbname]

    def create_generic_engine(self, url):
        return sa.create_engine(url)

    def create_sqlite_engine(self, url):
        engine = sa.create_engine(url)

        # Enable checking of foreign key constraints by setting
        # a pragma on each DB connection
        @event.listens_for(engine, "connect")
        def foreign_keys_on(dbapi_con, con_record):
            dbapi_con.execute("PRAGMA foreign_keys = ON")

        return engine

    def create_mysql_engine(self, url):
        url.query['use_unicode'] = "True"
        engine = sa.create_engine(url)

        @event.listens_for(engine, "connect")
        def foreign_keys_on(dbapi_con, con_record):
            # Set the default storage engine in case we create tables
            dbapi_con.cursor().execute("SET default_storage_engine=InnoDB")

        return engine

    @synchronized(threading.Lock())
    def session(self, dbname):
        # set up a session for each db; this uses scoped_session (based on the
        # thread ID) to ensure only one session per thread
        if dbname not in self._sessions:
            Session = orm.sessionmaker(bind=self.engine(dbname))
            self._sessions[dbname] = scoping.scoped_session(Session)
        return self._sessions[dbname]

    def flush_sessions(self):
        for s in self._sessions.values():
            s.remove()
        self._sessions = {}

    @property
    def database_names(self):
        return _declarative_bases.keys()

    @property
    def metadata(self):
        return dict((k, v.metadata) for k, v in _declarative_bases.iteritems())

# Pessimistically try *all* connections on checkout, in case the server has
# gone away.  This will apply to SQLite DBs too, where the server can't go
# away, but that's OK - SQLite is only used in development
#
# from
# http://docs.sqlalchemy.org/en/rel_0_9/core/pooling.html#disconnect-handling-pessimistic


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except Exception:  # pragma: no cover
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()


def make_db(app):
    return Alchemies(app)


class UTCDateTime(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            # Convert to UTC
            value = pytz.UTC.normalize(value.astimezone(pytz.UTC))
            # MySQL stores datetimes without any timezone information, similar
            # to a naive Python datetime.  Passing it a tz-aware datetime
            # causes a warning ("Out of range value for column .."), so we make
            # it naive.
            if dialect.name == 'mysql':
                value = value.replace(tzinfo=None)
        # else assume UTC
        return value

    def process_result_value(self, value, dialect):
        # We expect UTC dates back, so populate with tzinfo
        if value is not None:
            return value.replace(tzinfo=pytz.UTC)


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw, _test_hook=None):
    # Based on
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject
    cache = session.info.get('_unique_cache', None)
    if cache is None:
        session.info['_unique_cache'] = cache = {}

        # Setup to clear session cache on rollback
        @event.listens_for(session, "after_rollback", once=True)
        def _clear_session_cache(s):
            if s.info.get('_unique_cache', None):
                del s.info['_unique_cache']

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            if _test_hook:
                _test_hook()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
                session.flush()
        cache[key] = obj
        return obj


class UniqueMixin(object):
    # Based on
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
            session,
            cls,
            cls.unique_hash,
            cls.unique_filter,
            cls,
            arg, kw
        )
