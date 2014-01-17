import collections
import sqlalchemy as sa

class AppDb(object):
    """
    A container object that sits at app.db and handles access to metadata and
    connection pools.

    @ivar meta: dictionary of metadata instances for all defined databases, keyed
    by database name.  New instances are created on first access.

    @ivar database_names: a list of all defined database names
    """

    def __init__(self, app):
        self.app = app
        self.meta = collections.defaultdict(lambda: sa.MetaData())
        self._engines = {}

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
