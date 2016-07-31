# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask_sqlalchemy import SQLALchemy


def init_app(app):
    db = SQLALchemy()
    db.init_app(app)

    # ensure tables get created
    # TODO: for dbname in db.database_names:
    # TODO:     app.log.info("creating tables for database %s", dbname)

    # TODO:     meta = db.metadata[dbname]
    # TODO:     engine = db.engine(dbname)
    # TODO:     meta.create_all(bind=engine, checkfirst=True)

    @app.before_request
    def setup_request():
        g.db = app.db

    return db


