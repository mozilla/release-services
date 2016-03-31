# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import glob
import os
import shutil
import tempfile
from contextlib import contextmanager

import mock

import relengapi
from relengapi.lib import db
from relengapi.lib.testing.subcommands import run_main


@contextmanager
def copy_alembic_folder(dbname, copy=True):
    """ Copy the production config into a temporary folder without versions """
    temp_dir = tempfile.mkdtemp()
    try:
        if copy:
            src = os.path.join(os.path.dirname(relengapi.__file__), 'alembic', dbname)
            dest = os.path.join(temp_dir, dbname)
            shutil.copytree(src, dest)
            # remove all the current migrations in that folder for a clean slate
            files = glob.glob(os.path.join(dest, 'versions', '*'))
            for f in files:
                os.remove(f)
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def test_copy_alembic_folder_contains_config():
    """Our test helper should return a folder with a valid config"""
    dbname = 'relengapi'
    with copy_alembic_folder(dbname) as base_dir:
        config_file = os.path.join(base_dir, dbname, 'alembic.ini')
        assert os.path.isfile(config_file)


def test_copy_alembic_folder_empty_versions():
    """Our test helper should return a folder with empty versions"""
    dbname = 'relengapi'
    with copy_alembic_folder(dbname) as base_dir:
        versions = os.path.join(base_dir, dbname, 'versions')
        assert not os.listdir(versions)


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


def test_repl_command():
    output = run_main(["repl", '-c', 'print(app)\nprint("hello world")'])
    assert 'relengapi.app' in output  # from 'print(app)'
    assert 'hello world' in output  # from 'print("hello world")'


def test_sqs_listen():
    # this doesn't do much more than see that the AWS method is called;
    # that method is tested elsewhere
    with mock.patch("relengapi.lib.aws.AWS._spawn_sqs_listeners") as p:
        run_main(["sqs-listen"], settings={})
        p.assert_called_with()


def test_invalid_database_name():
    """show an error when we specify an invalid database name """
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        # create the revision
        output = run_main(["alembic", 'invalid_db_name', "--directory", base_dir, "revision"],
                          settings=settings)
        assert "specify a valid database name" in output


def test_invalid_configuration():
    """ When specifying a valid db that hasn't been initialized, we spit out an error message"""
    dbname = 'relengapi'
    uninit_db = 'clobberer'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        # create the revision
        output = run_main(["alembic", uninit_db, "--directory", base_dir, "revision"],
                          settings=settings)
        assert "Configuration file does not exist" in output


def test_alembic_revision():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        # create the revision
        output = run_main(["alembic", dbname, "--directory", base_dir, "revision"],
                          settings=settings)
        assert "Generating {}".format(base_dir) in output


def test_alembic_init():
    """ When we initialize a db, make sure that the ini exists """
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname, copy=False) as base_dir:
            run_main(["alembic", dbname, "--directory", base_dir, "init"], settings=settings)
            assert os.path.exists(os.path.join(base_dir, dbname, 'alembic.ini'))


def test_alembic_migrate():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicMigrateSubcommand.migrate") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "migrate"],
                     settings=settings)
            assert p.called


def test_alembic_upgrade():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicUpgradeSubcommand.upgrade") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "upgrade"],
                     settings=settings)
            assert p.called


def test_alembic_downgrade():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper."
                "AlembicDowngradeSubcommand.downgrade") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "downgrade"],
                     settings=settings)
            assert p.called


def test_alembic_stamp():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicStampSubcommand.stamp") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "stamp", "head"],
                     settings=settings)
            assert p.called


def test_alembic_current():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicCurrentSubcommand.current") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "current"],
                     settings=settings)
            assert p.called


def test_alembic_history():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicHistorySubcommand.history") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "history"],
                     settings=settings)
            assert p.called


def test_alembic_show():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicShowSubcommand.show") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "show", "head"],
                     settings=settings)
            assert p.called


def test_alembic_merge():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicMergeSubcommand.merge") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "merge", "head"],
                     settings=settings)
            assert p.called


def test_alembic_heads():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicHeadsSubcommand.heads") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "heads"],
                     settings=settings)
            assert p.called


def test_alembic_branches():
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper."
                "AlembicBranchesSubcommand.branches") as p:
            run_main(["alembic", dbname, "--directory", base_dir, "branches"],
                     settings=settings)
            assert p.called

# the run-tests command is in use to run these tests, so there's nothing additional to test.
