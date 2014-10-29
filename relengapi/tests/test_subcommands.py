# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from nose.tools import eq_
from relengapi.lib import subcommands
from relengapi.lib.testing.subcommands import run_main

logger = logging.getLogger(__name__)


class MySubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('my-subcommand', help='test subcommand')
        parser.add_argument("--result", help='Set result')
        return parser

    def run(self, parser, args):
        print "subcommand tests - print output"
        logger.info("subcommand tests - info logging output")
        logger.warning("subcommand tests - warning logging output")
        MySubcommand.run_result = args.result


def test_subcommand_help():
    assert 'my-subcommand' in run_main(['--help'])


def test_subcommand_runs():
    output = run_main(['my-subcommand', '--result=foo'])
    assert "print output" in output
    assert "info logging output" in output
    assert "warning logging output" in output
    eq_(MySubcommand.run_result, 'foo')


def test_subcommand_quiet():
    output = run_main(['--quiet', 'my-subcommand', '--result=foo'])
    assert "print output" in output
    assert "info logging output" not in output
    assert "warning logging output" in output
    eq_(MySubcommand.run_result, 'foo')
