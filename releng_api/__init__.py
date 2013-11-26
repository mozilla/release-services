from flask import Flask

def create_app():
    app = Flask('releng_api')
    app.config.from_envvar('RELENG_API_SETTINGS', silent=True)

    @app.route('/')
    def hello():
        return "Hello"

    return app
