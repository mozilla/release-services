from flask import Flask
from flask import redirect
from flask import url_for
from flask import current_app
from flask import jsonify
import pkg_resources

def create_app(cmdline=False):
    app = Flask('relengapi')
    app.config.from_envvar('RELENG_API_SETTINGS', silent=True)

    # get blueprints from pkg_resources
    for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
        if cmdline:
            print " * registering blueprint", ep.name
        app.register_blueprint(ep.load(), url_prefix='/%s' % ep.name)

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
