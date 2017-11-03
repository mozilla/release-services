# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json


def test_patch_status(client, bugs, header_bot):
    '''
    Fetch detailled analysis, with bugs
    '''
    from shipit_uplift.models import BugResult, PatchStatus
    url = '/bugs/1139560/patches'
    revision = '80c32af73390'  # existing patch revision
    branch = 'test'

    # Check patches in bug payload
    bug = BugResult.query.filter_by(bugzilla_id=1139560).one()
    patches = bug.payload_data['analysis']['patches']
    assert revision in patches
    assert 'merge' not in patches[revision]

    # Check there are no patch statuses at first
    resp = client.get(
        url,
        headers=[
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    statuses = json.loads(resp.data.decode('utf-8'))
    assert statuses == []

    # Add a patch status
    data = {
        'group': 1,
        'revision': revision,
        'revision_parent': '0000001',
        'branch': branch,
        'status': 'failed',
        'message': 'random mercurial error',
    }
    resp = client.post(
        url,
        data=json.dumps(data),
        headers=[
            ('Authorization', header_bot),
            ('Content-Type', 'application/json'),
        ],
    )
    assert resp.status_code == 200

    # Check we now have 1 patch status attached to the bug
    resp = client.get(
        url,
        headers=[
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    statuses = json.loads(resp.data.decode('utf-8'))
    assert len(statuses) == 1

    # Check patches in bug payload
    bug = BugResult.query.filter_by(bugzilla_id=1139560).one()
    patches = bug.payload_data['analysis']['patches']
    assert revision in patches
    assert 'merge' in patches[revision]
    assert patches[revision]['merge'] == {
        branch: False,
    }

    # Update existing patch status
    data['status'] = 'merged'
    data['message'] = 'Succesful merge!'
    resp = client.post(
        url,
        data=json.dumps(data),
        headers=[
            ('Authorization', header_bot),
            ('Content-Type', 'application/json'),
        ],
    )
    assert resp.status_code == 200
    ps = PatchStatus.query.filter_by(bug_id=bug.id, status='merged').one()
    assert ps.message == data['message']
