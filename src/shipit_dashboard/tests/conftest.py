import pytest
import pickle
import os
import glob
import json
from releng_common.mocks import build_header

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
    from shipit_dashboard.models import (
        BugAnalysis, BugResult, Contributor, BugContributor
    )
    from releng_common.db import db

    # Add 2 analysis
    analysis = []
    for i in ('A', 'B'):
        a = BugAnalysis(name='Analysis Test {}'.format(i))
        a.parameters = 'bugzilla=test'  # dummy params.
        db.session.add(a)
        analysis.append(a)

    # Add bugs with real payload
    paths = glob.glob(os.path.join(FIXTURES_DIR, 'bug_*.json'))
    sorted(paths)
    for path in paths:
        payload = json.load(open(path))
        bug = BugResult(bugzilla_id=payload['bug']['id'])
        bug.payload = pickle.dumps(payload, 2)
        analysis[0].bugs.append(bug)
        db.session.add(bug)

        # Add creator & link to bug
        user = payload['analysis']['users']['creator']
        contrib = Contributor(bugzilla_id=user['id'])
        contrib.name = user.get('real_name', user['name'])
        contrib.email = user['email']
        contrib.avatar_url = 'gravatar_url_here'
        contrib.karma = 1
        contrib.comment_private = 'hidden comment'
        contrib.comment_public = 'Top Contributor'
        link = BugContributor(bug=bug, contributor=contrib, roles='creator')
        db.session.add(contrib)
        db.session.add(link)

    db.session.commit()


def hawk_header(scopes):
    """"
    Helper to build an Hawk header
    for a set of TC scopes
    """
    client_id = 'test/shipit-user@mozilla.com'
    ext_data = {
        'scopes': scopes,
    }
    return build_header(client_id, ext_data)


@pytest.yield_fixture(scope='module')
def header_user(app):
    """
    Build an Hawk header for user role
    """
    from shipit_dashboard import SCOPES_USER
    return hawk_header(SCOPES_USER)


@pytest.yield_fixture(scope='module')
def header_admin(app):
    """
    Build an Hawk header for admin role
    """
    from shipit_dashboard import SCOPES_ADMIN
    return hawk_header(SCOPES_ADMIN)


@pytest.yield_fixture(scope='module')
def header_bot(app):
    """
    Build an Hawk header for bot role
    """
    from shipit_dashboard import SCOPES_BOT
    return hawk_header(SCOPES_BOT)
