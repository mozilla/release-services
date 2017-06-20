# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import cli_common.log
import flask
import flask_migrate
import flask_sqlalchemy
import os


logger = cli_common.log.get_logger(__name__)
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate(db=db)


def init_database(app):
    '''
    Run Migrations through Alembic
    '''
    migrations_dir = os.path.abspath(
        os.path.join(app.root_path, '..', 'migrations'))

    with app.app_context():

        # Needed to init potential migrations later on
        # Use a separate alembic_version table per app
        options = {
            'version_table': '{}_alembic_version'.format(app.db_prefix),
        }
        migrate.init_app(app, directory=migrations_dir, **options)

        if os.path.isdir(migrations_dir):
            logger.info('Starting migrations', app=app.name)
            try:
                flask_migrate.upgrade()
                logger.info('Completed migrations', app=app.name)
            except Exception as e:
                logger.error('Migrations failure', app=app.name, error=e)

        else:
            logger.info('No migrations: creating full DB', app=app.name)
            db.create_all()


ALLOWED_TABLES = [
    'relengapi_auth_tokens',
]


def init_app(app):
    app.db_prefix = app.name.replace('-', '_')
    db.init_app(app)

    # Check every table starts with app.db_prefix
    for table_name in db.metadata.tables.keys():
        if not table_name.startswith(app.db_prefix) and table_name not in ALLOWED_TABLES:
            raise Exception('DB table {} should start with {}'.format(table_name, app.db_prefix))

    # Try to run migrations on the app
    # or direct db creation
    init_database(app)

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db
