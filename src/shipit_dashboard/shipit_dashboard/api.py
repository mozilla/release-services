# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask import abort, request
from releng_common.auth import auth
from releng_common.db import db
from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.serializers import serialize_analysis, serialize_bug
from sqlalchemy import text
from sqlalchemy.orm.exc import NoResultFound
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

@auth.require_scopes([SCOPES_USER, SCOPES_BOT])
def list_analysis():
    """
    List all available analysis
    """
    all_analysis = BugAnalysis.query.all()
    return [serialize_analysis(analysis, False) for analysis in all_analysis]

@auth.require_scopes([SCOPES_USER, SCOPES_BOT])
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

@auth.require_scopes(SCOPES_USER)
def update_bug(bugzilla_id):
    """
    Update a bug after modifications on Bugzilla
    """
    # Load bug
    try:
        bug = BugResult.query.filter_by(bugzilla_id=bugzilla_id).one()
    except:
        raise Exception('Missing bug {}'.format(bugzilla_id))

    # Browse changes
    payload = bug.payload_data
    for update in request.json:

        if update['target'] == 'bug':
            # Update bug flags
            if update['bugzilla_id'] != bug.bugzilla_id:
                raise Exception('Invalid bugzilla_id in changes list') # should never happen
            for flag_name, actions in update['changes'].items():
                payload['bug'][flag_name] = actions.get('added')

        elif update['target'] == 'attachment':
            # Build flags map
            source = update['changes'].get('flagtypes.name', {})
            removed, added = source['removed'].split(', '), source['added'].split(', ')
            flags_map = dict(zip(removed, added))

            # Update attachment flag status
            for a in payload['bug']['attachments']:
                if a['id'] != update['bugzilla_id']:
                    continue
                for flag in a['flags']:
                    name = flag['name'] + flag['status']
                    if name in flags_map:
                        flag['status'] = flags_map[name][len(flag['name']):]

        else:
            raise Exception('Invalid update target {}'.format(update['target']))

    # Save changes
    bug.payload = pickle.dumps(payload, 2)
    db.session.add(bug)
    db.session.commit()

    # Send back the bug
    return serialize_bug(bug)

@auth.require_scopes(SCOPES_BOT)
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

@auth.require_scopes(SCOPES_BOT)
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
