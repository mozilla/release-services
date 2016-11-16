# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import structlog
import os
import flask
import flask_migrate
import flask_sqlalchemy

logger = structlog.get_logger('releng_common.db')
db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate(db=db)


def init_app(app):
    db.init_app(app)

    # Check every table starts with app_name
    for table_name in db.metadata.tables.keys():
        if not table_name.startswith(app.name):
            raise Exception('DB table {} should start with {}'.format(table_name, app.name))  # noqa

    # Setup migrations
    migrations_dir = os.path.abspath(
        os.path.join(app.root_path, '..', 'migrations'))

    # Setup migrations
    with app.app_context():
        options = {
            # Use a separate alembic_version table per app
            'version_table': '{}_alembic_version'.format(app.name),
        }
        migrate.init_app(app, directory=migrations_dir, **options)
        logger.info('Starting migrations', app=app.name)
        if os.path.isdir(migrations_dir):
            try:
                flask_migrate.upgrade()
                logger.info('Completed migrations', app=app.name)
            except Exception as e:
                logger.error('Migrations failure', app=app.name, error=e)
        else:
            flask_migrate.init()

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db
