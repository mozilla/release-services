from contextlib import closing
from relengapi.app import create_app

def make_parser(subparsers):
    parser = subparsers.add_parser('createdb', help='create configured databases')
    parser.set_defaults(run=run)

def run(args):
    app = create_app(cmdline=True)
    with app.app_context():
        for dbname in app.db.database_names:
            print " * creating tables for database %s" % (dbname,)
            meta = app.db.meta[dbname]
            print meta.tables.keys()
            with closing(app.db.connect(dbname)) as conn:
                meta.create_all(bind=conn)
