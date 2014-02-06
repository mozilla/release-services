import collections
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import scoping
from sqlalchemy.ext.declarative import declarative_base


_declarative_bases = collections.defaultdict(declarative_base)
def declarative_base(dbname):
    return _declarative_bases[dbname]


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
