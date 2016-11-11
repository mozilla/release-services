import pytest
import pickle
import os
import glob
import json

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.yield_fixture(scope='module')
def app():
    """
    Load shipit_dashboard app in test mode
    """
    # Set app in testing mode
    os.environ['APP_TESTING'] = 'shipit_dashboard'

    # Then import app code
    from releng_common.db import db
    from shipit_dashboard import app

    with app.app_context():
        # Init new database
        db.create_all()

        # Give app in its context
        yield app


@pytest.yield_fixture(scope='module')
def client(app):
    """
    A Flask test client for shipit_dashboard
    with mockups enabled
    """
    from releng_common import mocks

    # Give test client with mockups
    with app.test_client() as client:
        with mocks.apply_mockups():
            yield client


@pytest.yield_fixture(scope='module')
def bugs(app):
    """
    Add an analysis and some bugs
    """
    from shipit_dashboard.models import BugAnalysis, BugResult
    from releng_common.db import db

    # Add an analysis
    analysis = BugAnalysis(name='Analysis Test A')
    analysis.parameters = 'bugzilla=test'  # dummy params.
    db.session.add(analysis)

    # Add bugs with real payload
    paths = glob.glob(os.path.join(FIXTURES_DIR, 'bug_*.json'))
    sorted(paths)
    for path in paths:
        payload = json.load(open(path))
        bug = BugResult(bugzilla_id=payload['bug']['id'])
        bug.payload = pickle.dumps(payload, 2)
        analysis.bugs.append(bug)
        db.session.add(bug)

    db.session.commit()
