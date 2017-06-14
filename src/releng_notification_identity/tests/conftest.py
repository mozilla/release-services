import pytest
import os


@pytest.yield_fixture(scope='session')
def app():
    # Set app to testing mode
    os.environ['APP_TESTING'] = 'releng-notification-identity'

    # Import app code
    from backend_common.db import db
    from releng_notification_identity.flask import app

    # Create db and yield app
    with app.app_context():
        db.create_all()

        yield app


@pytest.yield_fixture(scope='session')
def client(app):
    from backend_common import mocks

    with app.test_client() as test_client:
        with mocks.apply_mockups():
            yield test_client
