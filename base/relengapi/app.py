# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from flask import Flask
from flask import g
from flask import render_template
from flask.ext.principal import Principal
from flask.ext.login import LoginManager
from relengapi import celery
from relengapi import db
from relengapi.lib import api
from relengapi.lib import monkeypatches
from relengapi.lib.actions import Actions
import pkg_resources
import relengapi

# set up the 'relengapi' namespace; it's a namespaced module, so no code
# is allowed in __init__.py
relengapi.login_manager = LoginManager()
relengapi.principal = Principal(use_sessions=True)
relengapi.actions = Actions()
relengapi.apimethod = api.apimethod

# apply monkey patches
monkeypatches.monkeypatch()

def create_app(cmdline=False, test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(**test_config)
    else:
        app.config.from_envvar('RELENGAPI_SETTINGS')

    # add the necessary components to the app
    app.db = db.make_db(app)
    app.celery = celery.make_celery(app)
    relengapi.principal.init_app(app)
    relengapi.login_manager.init_app(app)
    api.init_app(app)

    # get blueprints from pkg_resources
    for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
        if cmdline:
            print " * registering blueprint", ep.name
        app.register_blueprint(ep.load(), url_prefix='/%s' % ep.name)

    # set up a random session key if none is specified
    if not app.config.get('SECRET_KEY'):
        print " * WARNING: setting per-process session key"
        app.secret_key = os.urandom(24)

    @app.before_request
    def add_db():
        g.db = app.db

    @app.route('/')
    def root():
        # render all of the blueprints' templates first
        bp_widgets = []
        for bp in app.blueprints.itervalues():
            bp_widgets.extend(bp.root_widget_templates or [])
        bp_widgets.sort()
        bp_widgets = [tpl for (p, tpl) in bp_widgets]
        return render_template('root.html', bp_widgets=bp_widgets)

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
