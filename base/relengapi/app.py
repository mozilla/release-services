import os
from flask import current_app
from flask import Flask
from flask import g
from flask import jsonify
from flask import redirect
from flask import url_for
from flask_oauthlib.provider import OAuth2Provider
from relengapi import celery
from relengapi import db
import pkg_resources
import relengapi

# set up the 'relengapi' namespace; it's a namespaced module, so no code is allowed in __init__.py
relengapi.oauth = OAuth2Provider()

def create_app(cmdline=False):
    app = Flask('relengapi')
    app.config.from_envvar('RELENG_API_SETTINGS')

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

    @app.before_request
    def add_db():
        g.db = app.db

    @app.route('/')
    def root():
        return redirect(url_for('docs.root'))

    @app.route('/meta')
    def meta():
        "API: Metadata about this RelengAPI instance"
        meta = {}
        meta['blueprints'] = current_app.blueprints.keys()
        return jsonify(meta)

    return app
