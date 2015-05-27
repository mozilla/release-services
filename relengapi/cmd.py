# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import logging.handlers
import os
import relengapi.app
import sys

from relengapi.lib import subcommands


def setupConsoleLogging(quiet):
    root = logging.getLogger('')
    if quiet:
        root.setLevel(logging.WARNING)
    else:
        root.setLevel(logging.NOTSET)
    formatter = logging.Formatter('%(asctime)s %(message)s')

    stdout_log = logging.StreamHandler(sys.stdout)
    stdout_log.setLevel(logging.DEBUG)
    stdout_log.setFormatter(formatter)
    root.addHandler(stdout_log)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Releng API Command Line Tool")
    parser.add_argument("--quiet", '-q', action='store_true',
                        help="Silence all logging below WARNING level")
    subparsers = parser.add_subparsers(help='sub-command help')

    # each of the Subcommand subclasses was loaded when the blueprints were
    # imported in relengapi.app
    cmds = [cls() for cls in subcommands.Subcommand.__subclasses__()]
    for cmd in cmds:
        subparser = cmd.make_parser(subparsers)
        subparser.set_defaults(_subcommand=cmd)

    args = parser.parse_args(args)

    if args._subcommand and args._subcommand.want_logging:
        setupConsoleLogging(args.quiet)

    # make the RELENGAPI_SETTINGS env var an absolute path; without this, Flask
    # uses the application's root_dir, which isn't especially helpful in a
    # development context.
    var_name = 'RELENGAPI_SETTINGS'
    if var_name in os.environ:
        os.environ[var_name] = os.path.abspath(os.environ[var_name])

    app = relengapi.app.create_app(cmdline=True)
    with app.app_context():
        args._subcommand.run(parser, args)
