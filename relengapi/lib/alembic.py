# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import current_app

from relengapi import app


def env_py_main(context, dbname):
    config = context.config
    config.set_main_option('sqlalchemy.url', current_app.db._get_db_config(dbname))

    with app.create_app(cmdline=True).app_context():
        if context.is_offline_mode():
            run_migrations_offline(context, config, dbname)
        else:
            run_migrations_online(context, config, dbname)


def get_configure_args(config, dbname):
    args = {}
    # version table is always named after the dbname, so that multiple
    # dbnames can be put in the same database (e.g., for development)
    args['version_table'] = '{}_version'.format(dbname)
    return args


def run_migrations_offline(context, config, dbname):
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        **get_configure_args(config, dbname)
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(context, config, dbname):
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    target_metadata = current_app.db.metadata[dbname]

    engine = current_app.db.engine(dbname)
    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        **get_configure_args(config, dbname)
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()
