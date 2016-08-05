# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import g
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    db.create_all(app=app)

    @app.before_request
    def setup_request():
        g.db = app.db

    return db
