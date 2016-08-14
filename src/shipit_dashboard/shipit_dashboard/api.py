# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis
from sqlalchemy.orm.exc import NoResultFound
from flask import abort

def _serialize_analysis(analysis):
    """
    Helper to serialize an analysis
    """
    return {
        'id': analysis.id,
        'name': analysis.name,
        'bugs': [{
            'id': b.id,
            'bugzilla_id': b.bugzilla_id,
            'payload': b.payload_data,
        } for b in analysis.bugs if b.payload],
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
