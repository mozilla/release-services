from contextlib import closing
from relengapi import db
from relengapi import subcommands
from flask import Blueprint
from flask import current_app
from . import models

bp = Blueprint('base', __name__)

db.register_model(bp, 'relengapi')(models.relengapi_model)
db.register_model(bp, 'scheduler')(models.scheduler_model)


class ServeSubcommand(subcommands.Subcommand):
    
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('serve', help='run the server')
        parser.add_argument("-a", "--all-interfaces", action='store_true',
                            help='Run on all interfaces, not just localhost')
        parser.add_argument("-p", "--port", type=int, default=5000,
                            help='Port on which to serve')
        parser.add_argument("--no-debug", action='store_true',
                            help="Don't run in debug mode")
        return parser

    def run(self, parser, args):
        kwargs = {}
        if args.all_interfaces:
            kwargs['host'] = '0.0.0.0'
        kwargs['debug'] = not args.no_debug
        kwargs['port'] = args.port
        current_app.run(**kwargs)


class CreateDBSubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('createdb', help='create configured databases')
        return parser

    def run(self, parser, args):
        for dbname in current_app.db.database_names:
            print " * creating tables for database %s" % (dbname,)
            meta = current_app.db.meta[dbname]
            print meta.tables.keys()
            with closing(current_app.db.connect(dbname)) as conn:
                meta.create_all(bind=conn)
