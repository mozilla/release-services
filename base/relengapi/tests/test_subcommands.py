# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

from cStringIO import StringIO
from nose.tools import eq_
from relengapi import subcommands


class MySubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('my-subcommand', help='test subcommand')
        parser.add_argument("--result", help='Set result')
        return parser

    def run(self, parser, args):
        print "subcommand running"
        MySubcommand.run_result = args.result


def run_main(args):
    old_out = sys.stdout
    sys.stdout = fake_stdout = StringIO()
    try:
        subcommands.main(args)
    except SystemExit:
        pass
    finally:
        old_out.write(sys.stdout.getvalue())
        sys.stdout = old_out
    return fake_stdout.getvalue()


def test_subcommand_help():
    assert 'my-subcommand' in run_main(['--help'])


def test_subcommand_runs():
    assert "subcommand running" in run_main(['my-subcommand', '--result=foo'])
    eq_(MySubcommand.run_result, 'foo')
