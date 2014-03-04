# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi import subcommands
from flask import Blueprint
from flask import current_app


bp = Blueprint('base', __name__)


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
            meta = current_app.db.metadata[dbname]
            engine = current_app.db.engine(dbname)
            meta.create_all(bind=engine)
