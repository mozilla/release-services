# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import copy
import pytest
import pickle
import os
import glob
import json

import backend_common.testing
from backend_common.mocks import build_header


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.yield_fixture(scope='session')
def app():
    '''
    Load shipit_uplift app in test mode
    '''
    import shipit_uplift

    app_config = copy.deepcopy(backend_common.testing.app_config)
    app_config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })
    app = shipit_uplift.create_app(app_config)

    with app.app_context():
        backend_common.testing.clear_app(app)
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


@pytest.yield_fixture(scope='session')
def bugs(app):
    '''
    Add an analysis and some bugs
    '''
    from shipit_uplift.models import (
        BugAnalysis, BugResult, Contributor, BugContributor
    )
    from backend_common.db import db

    # Add 2 analysis
    analysis = []
    for i in ('Dev', 'Release'):
        a = BugAnalysis(name=i)
        a.version = 1  # dummy version
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
    ''''
    Helper to build an Hawk header
    for a set of TC scopes
    '''
    client_id = 'test/shipit-user@mozilla.com'
    ext_data = {
        'scopes': scopes,
    }
    return build_header(client_id, ext_data)


@pytest.yield_fixture(scope='session')
def header_user(app):
    '''
    Build an Hawk header for user role
    '''
    from shipit_uplift.config import SCOPES_USER
    return hawk_header(SCOPES_USER)


@pytest.yield_fixture(scope='session')
def header_admin(app):
    '''
    Build an Hawk header for admin role
    '''
    from shipit_uplift.config import SCOPES_ADMIN
    return hawk_header(SCOPES_ADMIN)


@pytest.yield_fixture(scope='session')
def header_bot(app):
    '''
    Build an Hawk header for bot role
    '''
    from shipit_uplift.config import SCOPES_BOT
    return hawk_header(SCOPES_BOT)
