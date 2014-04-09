# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from flask import Flask
from flask import g
from flask import render_template
from flask_oauthlib.provider import OAuth2Provider
from relengapi import celery
from relengapi import db
from relengapi import api
import pkg_resources
import relengapi

# set up the 'relengapi' namespace; it's a namespaced module, so no code
# is allowed in __init__.py
relengapi.oauth = OAuth2Provider()


def create_app(cmdline=False, test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(**test_config)
    else:
        app.config.from_envvar('RELENGAPI_SETTINGS')

    # get blueprints from pkg_resources
    for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
        if cmdline:
            print " * registering blueprint", ep.name
        app.register_blueprint(ep.load(), url_prefix='/%s' % ep.name)

    # set up a random session key if none is specified
    if not app.config.get('SECRET_KEY'):
        print " * WARNING: setting per-process session key"
        app.secret_key = os.urandom(24)

    # add the necessary components to the app
    app.db = db.make_db(app)
    app.celery = celery.make_celery(app)
    relengapi.oauth.init_app(app)
    api.init_app(app)

    @app.before_request
    def add_db():
        g.db = app.db

    @app.route('/')
    def root():
        return render_template('root.html')

    @app.route('/versions')
    @api.apimethod()
    def versions():
        dists = {}
        for dist in pkg_resources.WorkingSet():
            dists[dist.key] = {
                'project_name': dist.project_name,
                'version': dist.version,
            }
        blueprints = {}
        for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
            blueprints[ep.name] = {
                'distribution': ep.dist.key,
                'version': ep.dist.version,
            }
        return dict(distributions=dists, blueprints=blueprints)

    return app
