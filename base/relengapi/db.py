import collections
import sqlalchemy as sa

class Alchemies(object):
    """
    A container that handles access to SQLALchemy metadata and connection
    pools.  This is available in requests at g.db.

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

def make_db(app):
    return Alchemies(app)

def register_model(bp, dbname):
    """Register the decorated method to be called when setting up the database
    schema for the given database."""
    def wrap(fn):
        @bp.record
        def register_tables(state):
            meta = state.app.db.meta[dbname]
            fn(meta)
    return wrap
