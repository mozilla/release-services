from flask import Flask
from flask import redirect
from flask import url_for
import pkg_resources

def create_app():
    app = Flask('releng_api')
    app.config.from_envvar('RELENG_API_SETTINGS', silent=True)

    # get blueprints from pkg_resources
    for ep in pkg_resources.iter_entry_points('releng_api_blueprints'):
        app.register_blueprint(ep.load(), url_prefix='/%s' % ep.name)

    @app.route('/')
    def root():
        return redirect(url_for('docs.root'))

    return app
