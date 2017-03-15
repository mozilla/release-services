import pytest
from flask_login import current_user
from flask import jsonify
from backend_common import create_app, auth, mocks


@pytest.fixture(scope='module')
def app():
    """
    Build an app with an authenticated dummy api
    """

    # Use unique auth instance
    config = {
        'DEBUG': True,
    }
    app = create_app('test', extensions=[auth], config=config)

    @app.route('/')
    def index():
        return app.response_class('OK')

    @app.route('/test-login')
    @auth.auth.require_login
    def logged_in():
        data = {
            'auth': True,
            'user': current_user.get_id(),
            'scopes': current_user.permissions,
        }
        return jsonify(data)

    @app.route('/test-scopes')
    @auth.auth.require_scopes([
        ['project/test/A', 'project/test/B'],
        ['project/test-admin/*'],
    ])
    def scopes():
        return app.response_class('Your scopes are ok.')

    # Add fake swagger url, used by redirect
    app.api.swagger_url = '/'

    return app


@pytest.yield_fixture(scope='module')
def client(app):
    """
    A Flask test client.
    """
    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client
