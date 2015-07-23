# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import mock
import os
import relengapi
import shutil
import tempfile

from contextlib import contextmanager
from relengapi.lib import db
from relengapi.lib.testing.subcommands import run_main


@contextmanager
def copy_alembic_folder(dbname):
    """ Copy the production config into a temporary folder without versions """
    temp_dir = tempfile.mkdtemp()
    try:
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


def test_sqs_listen():
    # this doesn't do much more than see that the AWS method is called;
    # that method is tested elsewhere
    with mock.patch("relengapi.lib.aws.AWS._spawn_sqs_listeners") as p:
        run_main(["sqs-listen"], settings={})
        p.assert_called_with()


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
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicInitSubcommand.init") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "init"], settings=settings)
            assert p.called


def test_alembic_migrate():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicMigrateSubcommand.migrate") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "migrate"],
                     settings=settings)
            assert p.called


def test_alembic_upgrade():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicUpgradeSubcommand.upgrade") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "upgrade"],
                     settings=settings)
            assert p.called


def test_alembic_downgrade():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper."
                "AlembicDowngradeSubcommand.downgrade") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "downgrade"],
                     settings=settings)
            assert p.called


def test_alembic_stamp():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicStampSubcommand.stamp") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "stamp", "head"],
                     settings=settings)
            assert p.called


def test_alembic_current():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicCurrentSubcommand.current") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "current"],
                     settings=settings)
            assert p.called


def test_alembic_history():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicHistorySubcommand.history") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "history"],
                     settings=settings)
            assert p.called


def test_alembic_show():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicShowSubcommand.show") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "show", "head"],
                     settings=settings)
            assert p.called


def test_alembic_merge():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicMergeSubcommand.merge") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "merge", "head"],
                     settings=settings)
            assert p.called


def test_alembic_heads():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper.AlembicHeadsSubcommand.heads") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "heads"],
                     settings=settings)
            assert p.called


def test_alembic_branches():
    """ When creating a revision, a migration script should exist with the current head"""
    dbname = 'relengapi'
    settings = {'SQLALCHEMY_DATABASE_URIS': {}}
    for name in db._declarative_bases:
        settings['SQLALCHEMY_DATABASE_URIS'][name] = 'sqlite:///'  # in-memory
    run_main(["createdb"], settings=settings)
    with copy_alembic_folder(dbname) as base_dir:
        with mock.patch(
                "relengapi.blueprints.base.alembic_wrapper."
                "AlembicBranchesSubcommand.branches") as p:
            # create the revision
            run_main(["alembic", dbname, "--directory", base_dir, "branches"],
                     settings=settings)
            assert p.called

# the run-tests command is in use to run these tests, so there's nothing additional to test.
