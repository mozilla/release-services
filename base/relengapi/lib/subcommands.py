# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import logging.handlers
import pkg_resources
import relengapi.app
import sys


def setupConsoleLogging():
    root = logging.getLogger('')
    root.setLevel(logging.NOTSET)
    formatter = logging.Formatter('%(asctime)s %(message)s')

    stdout_log = logging.StreamHandler(sys.stdout)
    stdout_log.setLevel(logging.DEBUG)
    stdout_log.setFormatter(formatter)
    root.addHandler(stdout_log)


class Subcommand(object):

    want_logging = True

    def make_parser(self, subparsers):
        raise NotImplementedError

    def run(self, parser, args):
        pass


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Releng API Command Line Tool")
    subparsers = parser.add_subparsers(help='sub-command help')

    # load each of the blueprints; this defines the subcommand classes.  Note that
    # create_app does this again.
    for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
        ep.load()

    subcommands = [cls() for cls in Subcommand.__subclasses__()]
    for subcommand in subcommands:
        subparser = subcommand.make_parser(subparsers)
        subparser.set_defaults(_subcommand=subcommand)

    args = parser.parse_args(args)

    if args._subcommand and args._subcommand.want_logging:
        setupConsoleLogging()

    app = relengapi.app.create_app(cmdline=True)
    with app.app_context():
        args._subcommand.run(parser, args)
