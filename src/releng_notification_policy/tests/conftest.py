import pytest
import os


@pytest.yield_fixture(scope='session')
def app():
    # Set app to testing mode
    os.environ['APP_TESTING'] = 'releng-notification-policy'

    # Import app code
    from backend_common.db import db
    from releng_notification_policy.flask import app

    # Create db and yield app
    with app.app_context():
        db.create_all()
        app.config['RELENG_NOTIFICATION_IDENTITY_ENDPOINT'] = 'https://fake_endpoint.mozilla-releng.net'
        yield app


@pytest.yield_fixture(scope='session')
def client(app):
    from backend_common import mocks

    with app.test_client() as test_client:
        with mocks.apply_mockups():
            yield test_client
