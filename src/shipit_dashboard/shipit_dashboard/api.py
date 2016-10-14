# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.serializers import serialize_analysis, serialize_bug
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import text
from releng_common.auth import scopes_required
from releng_common.db import db
from flask import abort, request
import pickle

# Tasckcluster scopes
SCOPES_USER = [
    'project:shipit:user',
    'project:shipit:analysis/use',
    'project:shipit:bugzilla'
]
SCOPES_BOT = [
    'project:shipit:bot',
    'project:shipit:analysis/manage',
]

@scopes_required([SCOPES_USER, SCOPES_BOT])
def list_analysis():
    """
    List all available analysis
    """
    all_analysis = BugAnalysis.query.all()
    return [serialize_analysis(analysis, False) for analysis in all_analysis]

@scopes_required([SCOPES_USER, SCOPES_BOT])
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

@scopes_required([SCOPES_USER])
def update_bug(bug_id):
    """
    Update a bug after modified on Bugzilla
    NOT USED ATM
    """
    # Load bug
    try:
        bug = BugResult.query.filter_by(id=bug_id).one()
    except:
        raise Exception('Missing bug {}'.format(bug_id))

    # TODO: update bug in database to mark it as updated

    # Send back the bug
    return serialize_bug(bug)

@scopes_required([SCOPES_BOT])
def create_bug():
    """
    Create a new bug, or update its payload
    """
    # Load bug
    bugzilla_id = request.json.get('bugzilla_id')
    if not bugzilla_id:
        raise Exception('Missing bugzilla id')
    try:
        bug = BugResult.query.filter_by(bugzilla_id=bugzilla_id).one()
    except:
        bug = BugResult(bugzilla_id=bugzilla_id)

    # Load all analysis
    analysis_ids = request.json.get('analysis', [])
    analysis = BugAnalysis.query.filter(BugAnalysis.id.in_(analysis_ids)).all()
    if not analysis:
        raise Exception('No analysis found for {}'.format(analysis_ids))

    # Update bug payload
    payload = request.json.get('payload')
    payload_hash = request.json.get('payload_hash')
    if not payload or not payload_hash:
        raise Exception('Missing payload updates.')
    bug.payload = pickle.dumps(payload, 2)
    bug.payload_hash = payload_hash


    # Attach bug to its analysis
    for a in analysis:
        a.bugs.append(bug)

    # Save all changes
    db.session.add(bug)
    db.session.commit()

    # Send back the bug
    return serialize_bug(bug)

@scopes_required([SCOPES_BOT])
def delete_bug(bugzilla_id):
    """
    Delete a bug when it's not in Bugzilla analysis
    """
    # Load bug
    try:
        bug = BugResult.query.filter_by(bugzilla_id=bugzilla_id).one()
    except:
        raise Exception('Missing bug {}'.format(bugzilla_id))

    # Delete links, avoid StaleDataError
    db.engine.execute(text('delete from analysis_bugs where bug_id = :bug_id'), bug_id=bug.id)

    # Delete the bug
    db.session.delete(bug)
    db.session.commit()
