# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.serializers import serialize_analysis, serialize_bug
from sqlalchemy.orm.exc import NoResultFound
from flask_login import login_required, current_user
from flask import abort, request
from datetime import datetime, timedelta
import requests

BUGZILLA_SECRET = 'project:shipit/{}/bugzilla'

def check_bugzilla_auth(login, token):
    """
    Check the bugzilla auth is working
    """
    # TODO: do a patch to libmozdata upstream
    url = 'https://bugzilla.mozilla.org/rest/valid_login'
    params = {
        'login' : login,
    }
    headers = {
        'X-Bugzilla-Api-Key' : token,
    }
    resp = requests.get(url, params=params, headers=headers)
    return resp.ok and resp.content == b'true'

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
    try:
        secret_name = BUGZILLA_SECRET.format(current_user.get_id())
        auth = current_user.get_secret(secret_name)

        # Check the auth is still valid
        if not check_bugzilla_auth(auth['login'], auth['token']):
            return {
                'authenticated': False,
                'message' : 'Invalid bugzilla auth',
            }

        return {
            'authenticated': True,
            'message' : 'Valid authentication for {}'.format(auth['login']),
        }
    except:
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

    # Check the auth is still valid
    if not check_bugzilla_auth(login, token):
        raise Exception('Invalid bugzilla auth')

    # Store the auth in secret
    payload = {
        'secret': {
            'token' : token,
            'login' : login,
        },
        'expires' : datetime.now() + timedelta(days=365)
    }
    secrets = current_user.taskcluster_secrets()
    secret_name = BUGZILLA_SECRET.format(current_user.get_id())
    secrets.set(secret_name, payload)

    return {
        'authenticated': True,
        'message' : 'Valid authentication for {}.'.format(login),
    }

@login_required
def update_bug(bug_id):
    """
    Update a bug with new comment & flags values
    """
    # Load bug
    try:
        bug = BugResult.query.filter_by(id=bug_id).one()
    except:
        raise Exception('Missing bug {}'.format(bug_id))

    # Check mandatory input
    if 'comment' not in request.json:
        raise Exception('Missing comment')

    # Load bugzilla auth
    auth = current_user.get_secret(BUGZILLA_SECRET)

    # Build bugzilla request
    data = {
        'comment' : {
            'body' : request.json['comment'],
            'is_private' : False,
            'is_markdown' : False,
        },
        'comment_tags' :  ['shipit', ],
        'flags' : [],
    }

    # Add flags
    for k,v in request.json.items():
        if not (k.startswith('status') or k.startswith('tracking')):
            continue
        data['flags'].append({
            'name' : k,
            'status' : v,
        })

    # Send data to bugzilla
    print('DATA to update bug', data)
    url = 'https://bugzilla.mozilla.org/rest/bugs/{}'.format(bug.bugzilla_id)
    headers = {
        'X-Bugzilla-Api-Key' : auth['token'],
    }
    resp = requests.put(url, json=data, headers=headers)
    if not resp.ok:
        raise Exception('Invalid bugzilla response: {}'.format(resp.content))

    # TODO: update local version ?

    # Send back the bug
    return serialize_bug(bug)
