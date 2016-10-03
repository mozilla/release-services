# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.serializers import serialize_analysis, serialize_bug
from sqlalchemy.orm.exc import NoResultFound
from flask_login import current_user
from releng_common.auth import scopes_required
from flask import abort, request
from datetime import datetime, timedelta
import requests

BUGZILLA_SECRET = 'project:shipit/{}/bugzilla'

# Tasckcluster scopes
SCOPE_BASE = 'project:shipit:user'
SCOPE_ANALYSIS = 'project:shipit:analysis'
SCOPE_BUGZILLA = 'project:shipit:bugzilla'

@scopes_required([SCOPE_BASE, SCOPE_ANALYSIS])
def list_analysis():
    """
    List all available analysis
    """
    all_analysis = BugAnalysis.query.all()
    return [serialize_analysis(analysis, False) for analysis in all_analysis]

@scopes_required([SCOPE_BASE, SCOPE_ANALYSIS])
def get_analysis(analysis_id):
    """
    Fetch an analysis and all its bugs
    """

    # Get bug analysis
    try:
        analysis = BugAnalysis.query.filter_by(id=analysis_id).one()
    except NoResultFound:
        abort(404)

    # Build JSON output
    return serialize_analysis(analysis)

@scopes_required([SCOPE_BASE, SCOPE_BUGZILLA, SCOPE_ANALYSIS])
def update_bug(bug_id):
    """
    Update a bug with new comment & flags values
    """
    # Load bug
    try:
        bug = BugResult.query.filter_by(id=bug_id).one()
    except:
        raise Exception('Missing bug {}'.format(bug_id))

    # TODO: update bug in database to mark it as updated

    # Send back the bug
    return serialize_bug(bug)
