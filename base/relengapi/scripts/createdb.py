from relengapi.app import create_app

def make_parser(subparsers):
    parser = subparsers.add_parser('createdb', help='create configured databases')
    parser.set_defaults(run=run)

def run(args):
    app = create_app(cmdline=True)
    with app.app_context():
        from relengapi import db

        # note that this assumes that all of the relevant models have been
        # imported during app creation
        binds = [('base', None, app.config['SQLALCHEMY_DATABASE_URI'])]
        for bind, uri in app.config['SQLALCHEMY_BINDS'].iteritems():
            binds.append((bind, bind, uri))
        for name, bind, uri in binds:
            print " * creating tables for %s (%s)" % (name, uri)
            db.create_all(bind=bind)
