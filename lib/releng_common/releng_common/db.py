# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import logging
import os
import flask
import flask_migrate
import flask_sqlalchemy

logger = logging.getLogger('releng_common.db')
db = flask_sqlalchemy.SQLAlchemy()


def init_app(app):
    db.init_app(app)

    # Setup migrations
    migrations_dir = os.path.abspath(
        os.path.join(app.root_path, '..', 'migrations'))
    flask_migrate.Migrate(app, db, directory=migrations_dir)
    with app.app_context():
        if os.path.isdir(migrations_dir):
            try:
                flask_migrate.upgrade()
            except Exception as e:
                logger.error('Migrations failure: {}'.format(e))
        else:
            flask_migrate.init()

    @app.before_request
    def setup_request():
        flask.g.db = app.db

    return db
