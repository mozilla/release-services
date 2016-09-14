# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis
from shipit_dashboard.serializers import serialize_analysis
from sqlalchemy.orm.exc import NoResultFound
from flask_login import login_required, current_user
from flask import abort, request
from datetime import datetime, timedelta

BUGZILLA_SECRET = 'garbage/shipit/bugzilla'

@login_required
def list_analysis():
    """
    List all available analysis
    """
    all_analysis = BugAnalysis.query.all()
    return [serialize_analysis(analysis, False) for analysis in all_analysis]

@login_required
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

@login_required
def get_bugzilla_auth():
    """
    Checks if current user has an available
    and valid bugzilla auth token
    stored in Taskcluster secrets
    """
    secrets = current_user.taskcluster_secrets()
    auth_secret = secrets.get(BUGZILLA_SECRET)
    if auth_secret:
        # TODO : Check the auth is still valid
        return {
            'authenticated': True,
            'message' : 'Valid authentication for {}'.format(auth_secret['secret']['login']),
        }

    return {
        'authenticated': False,
        'message' : 'No authentication stored.',
    }

@login_required
def update_bugzilla_auth():
    """
    Update bugzilla token & login
    in Taskcluster secrets
    """
    token = request.json.get('token')
    login = request.json.get('login')
    if not (token and login):
      raise Exception('Missing token and login')

    # TODO : Check the auth is still valid

    # Store the auth in secret
    payload = {
        'secret': {
            'token' : token,
            'login' : login,
        },
        'expires' : datetime.now() + timedelta(days=365)
    }
    secrets = current_user.taskcluster_secrets()
    resp = secrets.set(BUGZILLA_SECRET, payload)
    print(resp)

    return {
        'authenticated': True,
        'message' : 'Valid authentication for {}.'.format(login),
    }

