"""Configure a mock application to run queries against"""

import pytest
from flask_login import current_user
from flask import jsonify
from backend_common import create_app, auth, auth0, mocks
from os.path import join, dirname

FAKE_CLIENT_SECRETS = """
{
    "web": {
        "auth_uri": "https://auth.mozilla.auth0.com/authorize",
        "issuer": "https://auth.mozilla.auth0.com/",
        "client_id": "some-id-string",
        "client_secret": "my-super-secret",
        "redirect_uris": [
            "https://signoff.shipit.mozilla.com/oidc_callback"
        ],
        "token_uri": "https://auth.mozilla.auth0.com/oauth/token",
        "token_introspection_uri": "https://test/oauth/token",
        "userinfo_uri": "https://auth.mozilla.auth0.com/userinfo"
    }
}
"""


@pytest.fixture(scope='module')
def app():
    """
    Build an app with an authenticated dummy api
    """

    # Use unique auth instance
    config = {
        'DEBUG': True,
        'OIDC_CLIENT_SECRETS': join(dirname(__file__), 'client_secrets.json'),
        'OIDC_RESOURCE_SERVER_ONLY': True
    }

    app = create_app('test', extensions=[auth, auth0], config=config)

    @app.route('/')
    def index():
        return app.response_class('OK')

    @app.route('/test-auth-login')
    @auth.auth.require_login
    def logged_in():
        data = {
            'auth': True,
            'user': current_user.get_id(),
            # permissions is a set, not serializable
            'scopes': list(current_user.permissions),
        }
        return jsonify(data)

    @app.route('/test-auth-scopes')
    @auth.auth.require_scopes([
        ['project/test/A', 'project/test/B'],
        ['project/test-admin/*'],
    ])
    def scopes():
        return app.response_class('Your scopes are ok.')

    @app.route('/test-auth0-userinfo')
    @auth0.accept_token()
    def auth0_token():
        return app.response_class('OK')

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
