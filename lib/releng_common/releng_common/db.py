# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os


db = SQLAlchemy()

def init_app(app):
    db.init_app(app)

    # Setup migrations
    migrations_dir = os.path.abspath(os.path.join(app.root_path, '..', 'migrations'))
    Migrate(app, db, directory=migrations_dir)

    @app.before_request
    def setup_request():
        g.db = app.db

    return db
