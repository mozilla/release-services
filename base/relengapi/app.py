from flask import Flask
from flask import g
from flask import redirect
from flask import url_for
from flask import current_app
from flask import jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import pkg_resources
import relengapi

# create the global 'relengapi.db' object; this can't be defined in __init__.py
# since that is a pkg_resources namespace package.  Note that this needs to
# occur before any model modules are loaded, as they subclass db.Model.
db = SQLAlchemy()
relengapi.db = db

def create_app(cmdline=False):
    app = Flask('relengapi')
    app.config.from_envvar('RELENG_API_SETTINGS')

    # get blueprints from pkg_resources
    for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
        if cmdline:
            print " * registering blueprint", ep.name
        app.register_blueprint(ep.load(), url_prefix='/%s' % ep.name)

    # set up Flask-SQLAlchemy
    db.init_app(app)
    @app.before_request
    def add_db():
        g.db = db

    @app.route('/')
    def root():
        return redirect(url_for('docs.root'))

    @app.route('/meta')
    def meta():
        "API: Metadata about this RelengAPI instance"
        meta = {}
        meta['blueprints'] = current_app.blueprints.keys()
        return jsonify(meta)

    @app.route('/testy')
    def testy():
        "Some DB test stuff"
        import relengapi.models.base as model
        testies = model.TestTable.query.all()
        return jsonify(testies)

    return app
