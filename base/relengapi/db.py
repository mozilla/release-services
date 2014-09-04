# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sqlalchemy as sa
import threading
import pytz
from relengapi.util import synchronized
from flask import current_app
from sqlalchemy import types
from sqlalchemy import orm
from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.orm import scoping
from sqlalchemy.ext import declarative


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
        app.teardown_request(self._teardown)

    @synchronized(threading.Lock())
    def engine(self, dbname):
        if dbname not in self._engines:
            uri = self.app.config['SQLALCHEMY_DATABASE_URIS'][dbname]
            self._engines[dbname] = sa.create_engine(uri)
        return self._engines[dbname]

    @synchronized(threading.Lock())
    def session(self, dbname):
        # set up a session for each db; this uses scoped_session (based on the
        # thread ID) to ensure only one session per thread
        if dbname not in self._sessions:
            Session = orm.sessionmaker(bind=self.engine(dbname))
            self._sessions[dbname] = scoping.scoped_session(Session)
        return self._sessions[dbname]

    def _teardown(self, response_or_exc):
        for s in self._sessions.values():
            s.remove()

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
# from http://docs.sqlalchemy.org/en/rel_0_9/core/pooling.html#disconnect-handling-pessimistic


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
        # else assume UTC
        return value

    def process_result_value(self, value, dialect):
        # We expect UTC dates back, so populate with tzinfo
        if value is not None:
            return value.replace(tzinfo=pytz.UTC)


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw, _test_hook=None):
    # Based on https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject
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
    # Based on https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/UniqueObject
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
