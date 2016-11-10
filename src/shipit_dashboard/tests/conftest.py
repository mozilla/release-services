import pytest
import os


@pytest.yield_fixture(scope='module')
def client():
    """
    A Flask test client for shipit_dashboard
    with mockups enabled
    """
    # Set app in testing mode
    os.environ['APP_TESTING'] = 'shipit_dashboard'

    # Then import app code
    from releng_common import mocks
    from releng_common.db import db
    from shipit_dashboard import app
    from shipit_dashboard.models import BugAnalysis

    with app.app_context():
        # Init new database
        db.create_all()

        # Add an analysis
        br = BugAnalysis(name='Analysis Test A')
        br.parameters = 'bugzilla=test' # dummy params.
        db.session.add(br)
        db.session.commit()

    # Give test client with mockups
    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client
