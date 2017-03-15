# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import structlog
import os
import flask
import flask_migrate
import flask_sqlalchemy
import logging  # for sql alchemy


logger = structlog.get_logger('backend_common.db')
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate(db=db)


def init_database(app):
    """
    Run Migrations through Alembic
    """
    migrations_dir = os.path.abspath(
        os.path.join(app.root_path, '..', 'migrations'))

    with app.app_context():

        # Needed to init potential migrations later on
        # Use a separate alembic_version table per app
        options = {
            'version_table': '{}_alembic_version'.format(app.name),
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


def init_app(app):
    db.init_app(app)

    # Check every table starts with app_name
    for table_name in db.metadata.tables.keys():
        if not table_name.startswith(app.name):
            raise Exception('DB table {} should start with {}'.format(table_name, app.name))  # noqa

    # Log queries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    # Try to run migrations on the app
    # or direct db creation
    init_database(app)

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db
