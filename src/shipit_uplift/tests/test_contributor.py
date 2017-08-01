# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json


def test_comments_user(client, header_user):
    '''
    A user must not have private comment
    in bugs details
    '''
    resp = client.get(
        '/analysis/1',
        headers=[('Authorization', header_user)],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 3
    contributors = analysis['bugs'][0]['contributors']
    assert len(contributors) == 1
    contrib = contributors[0]
    assert contrib['name'] == 'Mat Marquis'
    assert contrib['karma'] == 1
    assert contrib['comment_public'] == 'Top Contributor'
    assert 'comment_private' not in contrib


def test_comments_admin(client, header_admin):
    '''
    An admin must have private comment
    in bugs details
    '''
    resp = client.get(
        '/analysis/1',
        headers=[('Authorization', header_admin)],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 3
    contributors = analysis['bugs'][0]['contributors']
    assert len(contributors) == 1
    contrib = contributors[0]
    assert contrib['name'] == 'Mat Marquis'
    assert contrib['karma'] == 1
    assert contrib['comment_public'] == 'Top Contributor'
    assert contrib['comment_private'] == 'hidden comment'


def test_update_user(client, header_user):
    '''
    A user can't update a contributor
    '''
    from shipit_uplift.models import Contributor
    contrib = Contributor.query.filter_by(id=1).one()
    assert contrib.karma == 1
    assert contrib.comment_private == 'hidden comment'
    assert contrib.comment_public == 'Top Contributor'

    data = {
        'karma': -1,
        'comment_public': 'Bad comment',
        'comment_private': 'Explanation',
    }
    resp = client.put(
        '/contributor/1',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_user),
        ],
    )
    assert resp.status_code == 401
    error = json.loads(resp.data.decode('utf-8'))
    assert error['title'] == '401 Unauthorized: Invalid user scopes'

    contrib = Contributor.query.filter_by(id=1).one()
    assert contrib.karma == 1
    assert contrib.comment_private == 'hidden comment'
    assert contrib.comment_public == 'Top Contributor'


def test_update_admin(client, header_admin):
    '''
    An admin can update a contributor
    '''
    from shipit_uplift.models import Contributor
    contrib = Contributor.query.filter_by(id=1).one()
    assert contrib.karma == 1
    assert contrib.comment_private == 'hidden comment'
    assert contrib.comment_public == 'Top Contributor'

    data = {
        'karma': -1,
        'comment_public': 'Bad comment',
        'comment_private': 'Explanation',
    }
    resp = client.put(
        '/contributor/1',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_admin),
        ],
    )
    assert resp.status_code == 200
    output = json.loads(resp.data.decode('utf-8'))
    assert output['comment_private'] == 'Explanation'
    assert output['comment_public'] == 'Bad comment'
    assert 'roles' not in output

    contrib = Contributor.query.filter_by(id=1).one()
    assert contrib.karma == -1
    assert contrib.comment_private == 'Explanation'
    assert contrib.comment_public == 'Bad comment'
