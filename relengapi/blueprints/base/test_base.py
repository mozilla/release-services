# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import mock

from relengapi.lib import db
from relengapi.lib.testing.subcommands import run_main


def test_serve():
    with mock.patch("flask.Flask.run") as run:
        run_main(["serve"])
        run.assert_called_with(debug=True, port=5000)


def test_serve_all_interfaces():
    with mock.patch("flask.Flask.run") as run:
        run_main(["serve", "-a"])
        run.assert_called_with(debug=True, port=5000, host='0.0.0.0')


def test_serve_port():
    with mock.patch("flask.Flask.run") as run:
        run_main(["serve", "-p", "8010"])
        run.assert_called_with(debug=True, port=8010)


def test_serve_no_debug():
    with mock.patch("flask.Flask.run") as run:
        run_main(["serve", "--no-debug"])
        run.assert_called_with(debug=False, port=5000)


def test_createdb():
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for dbname in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][dbname] = 'sqlite:///'  # in-memory
    output = run_main(["createdb"], settings=settings)
    assert 'creating tables for database relengapi' in output


def test_sqs_listen():
    # this doesn't do much more than see that the AWS method is called;
    # that method is tested elsewhere
    with mock.patch("relengapi.lib.aws.AWS._spawn_sqs_listeners") as p:
        run_main(["sqs-listen"], settings={})
        p.assert_called_with()

# the run-tests command is in use to run these tests, so there's nothing additional to test.
