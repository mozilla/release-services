import pytest
from releng_common import create_app, auth
import json
import responses


def taskcluster_auth_mock(request):
    """
    Mock the hawk header validation from Taskcluster
    """
    # TODO: analyse the payload
    # payload = json.loads(request.body)
    body = {
        'status': 'auth-success',
        'scopes': [],
        'scheme': 'hawk',
        'clientId': 'test/test@mozilla.com',
        'expires': '2017-01-01T00:00:00',
    }
    headers = {}
    return (200, headers, json.dumps(body))

responses.add_callback(
    responses.POST, 'https://auth.taskcluster.net/v1/authenticate-hawk',
    callback=taskcluster_auth_mock,
    content_type='application/json',
)


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
        return app.response_class('Authenticated')

    return app


@pytest.yield_fixture(scope='module')
def client(app):
    """
    A Flask test client.
    """
    with app.test_client() as client:
        yield client
