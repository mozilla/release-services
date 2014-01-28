import collections
from werkzeug.local import LocalProxy
from flask import current_app
import sqlalchemy as sa

_registered_tables = {}
def Table(dbname_tablename, *args, **kwargs):
    """
    Create a per-app proxy to a sqlalchemy.Table object.
    """
    assert dbname_tablename.count(':') == 1, "Table must be called with 'dbname:tablename'"
    _registered_tables[dbname_tablename] = (args, kwargs)
    return LocalProxy(lambda: current_app.db.tables[dbname_tablename])


class Alchemies(object):
    """
    A container that handles access to SQLALchemy metadata and connection
    pools.  This is available in requests at g.db.

    @ivar meta: dictionary of metadata instances for all defined databases, keyed
    by database name.  New instances are created on first access.

    @ivar database_names: a list of all defined database names

    @ivar tables: a dictionary of Table instances, keyed by 'dbname:tablename' strings
    or at two levels e.g., ``g.db.tables['somedb']['sometable']``
    """

    def __init__(self, app):
        self.app = app
        self.meta = collections.defaultdict(lambda: sa.MetaData())
        self.tables = {}
        self._engines = {}

        # instantiate table instances for all registered tables
        for dbname_tablename, (args, kwargs) in _registered_tables.iteritems():
            dbname, tablename = dbname_tablename.split(':')
            tbl = sa.Table(tablename, self.meta[dbname], *args, **kwargs)
            self.tables[dbname_tablename] = tbl
            self.tables.setdefault(dbname, {})[tablename] = tbl

    def connect(self, dbname):
        "Check out an SQLAlchemy connection to the given DB from the pool"
        # TODO: attach to app context and close after
        if dbname not in self._engines:
            uri = self.app.config['SQLALCHEMY_DATABASE_URIS'][dbname]
            self._engines[dbname] = sa.create_engine(uri)
        conn = self._engines[dbname].connect()
        return conn

    @property
    def database_names(self):
        return self.meta.keys()

def make_db(app):
    return Alchemies(app)
