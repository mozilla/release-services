import pytest
import tempfile
import os
from releng_common import mocks
import shutil


@pytest.yield_fixture(scope='module')
def client():
    """
    A Flask test client for shipit_dashboard
    with mockups enabled
    """
    temp_dir = tempfile.mkdtemp(suffix='test_workdir')
    temp_settings = os.path.join(temp_dir, 'settings.py')

    # Setup settings before loading app
    with open(temp_settings, 'w') as f:
        f.write('DEBUG = True\n')
        f.write('TESTING = True\n')
        f.write('SERVER_NAME = "localhost:8010"\n')

        # In memory sqlite
        f.write('DATABASE_URL = "sqlite://"\n')
        f.write('SQLALCHEMY_DATABASE_URI = "sqlite://"\n')
        f.write('SQLALCHEMY_TRACK_MODIFICATIONS = True\n')
        f.write('CACHE_DEFAULT_TIMEOUT = 3600\n')
        f.write('CACHE_TYPE = "filesystem"\n')
        f.write('CACHE_DIR = "{}/cache"\n'.format(temp_dir))
        f.write('SWAGGER_BASE_URL = "/"\n')
    os.environ['APP_SETTINGS'] = temp_settings

    # Load app and init database
    from shipit_dashboard import app
    from releng_common.db import db
    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client

    # Cleanup
    shutil.rmtree(temp_dir)
