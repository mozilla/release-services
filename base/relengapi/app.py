import os
from flask import Flask
from flask import g
from flask import render_template
from flask_oauthlib.provider import OAuth2Provider
from relengapi import celery
from relengapi import db
from flask.ext.login import LoginManager
from flask.ext.browserid import BrowserID
import pkg_resources
import relengapi

# set up the 'relengapi' namespace; it's a namespaced module, so no code is allowed in __init__.py
relengapi.oauth = OAuth2Provider()
relengapi.login_manager = LoginManager()
relengapi.browser_id = BrowserID()

def create_app(cmdline=False):
    app = Flask(__name__)
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
    relengapi.login_manager.init_app(app)

    # this is ugly..
    app.config['BROWSERID_LOGIN_URL'] = '/userauth/login'
    app.config['BROWSERID_LOGOUT_URL'] = '/userauth/logout'
    relengapi.browser_id.init_app(app)

    @app.before_request
    def add_db():
        g.db = app.db

    @app.route('/')
    def root():
        return render_template('root.html')

    return app
