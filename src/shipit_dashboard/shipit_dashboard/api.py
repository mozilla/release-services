# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis
from sqlalchemy.orm.exc import NoResultFound
from flask import abort

def _serialize_bug(bug):
    """
    Helper to serialize a bug from its payload
    """
    payload = bug.payload_data
    if not payload:
        raise Exception('Missing payload')
    bug_data = payload.get('bug')
    analysis = payload.get('analysis')
    if not bug_data or not analysis:
        raise Exception('Missing Bug data or Analysis')

    # Build uplift
    uplift = None
    if analysis.get('uplift_comment') and analysis.get('uplift_author'):
        author = analysis['uplift_author']
        comment = analysis['uplift_comment']
        uplift = {
            'id' : comment['id'],
            'author' : {
                'email' : author['name'], # weird :/
                'real_name' : author['real_name'],
            },
            'comment' : comment['raw_text'],
        }

    return {
        # Base
        'id': bug.id,
        'bugzilla_id': bug.bugzilla_id,
        'summary' : bug_data['summary'],

        # Contributor structures
        'creator' : analysis['users']['creator'],
        'assignee' : analysis['users']['assignee'],
        'reviewers' : [{
            'email' : r,
            'real_name' : r,
        } for r in analysis['users']['reviewers']],

        # Stats
        'changes_size' : analysis.get('changes_size', 0),

        # Uplift request
        'uplift' : uplift,
    }

def _serialize_analysis(analysis):
    """
    Helper to serialize an analysis
    """
    return {
        'id': analysis.id,
        'name': analysis.name,
        'bugs': [_serialize_bug(b) for b in analysis.bugs if b.payload],
    }

def list_analysis():
    """
    List all available analysis
    """
    all_analysis = BugAnalysis.query.all()
    return [_serialize_analysis(analysis) for analysis in all_analysis]

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
    return _serialize_analysis(analysis)
