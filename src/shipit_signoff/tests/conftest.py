# -*- coding: utf-8 -*-
import pytest
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.yield_fixture(scope='session')
def app():
    '''
    Load shipit_uplift app in test mode
    '''
    # Set app in testing mode
    os.environ['APP_TESTING'] = 'shipit-signoff'

    # Then import app code
    from backend_common.db import db
    from shipit_signoff.flask import app

    with app.app_context():
        # Init new database
        db.drop_all()
        db.create_all()
        # Give app in its context
        yield app


@pytest.yield_fixture(scope='session')
def client(app):
    '''
    A Flask test client for shipit_uplift
    with mockups enabled
    '''
    from backend_common import mocks

    # Give test client with mockups
    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client
