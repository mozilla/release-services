# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import flask
import pytest


def test_anonymous():
    '''
    Test AnonymousUser instances
    '''
    import backend_common.auth

    user = backend_common.auth.AnonymousUser()

    # Test base
    assert user.get_id() == 'anonymous:'
    assert user.get_permissions() == set()
    assert user.permissions == set()
    assert not user.is_active
    assert user.is_anonymous


def test_taskcluster_user():
    '''
    Test TasklusterUser instances
    '''

    import backend_common.auth

    credentials = {
        'clientId': 'test/user@mozilla.com',
        'scopes': ['project:test:*', ]
    }
    user = backend_common.auth.TaskclusterUser(credentials)

    # Test base
    assert user.get_id() == credentials['clientId']
    assert user.get_permissions() == credentials['scopes']
    assert user.permissions == credentials['scopes']
    assert user.is_active
    assert not user.is_anonymous

    # Test invalid input
    with pytest.raises(AssertionError):
        user = backend_common.auth.TaskclusterUser({})
    with pytest.raises(AssertionError):
        user = backend_common.auth.TaskclusterUser({'clientId': '', 'scopes': None})


def test_auth(client):
    '''
    Test the Taskcluster authentication
    '''

    import backend_common.testing

    # Test non authenticated endpoint
    resp = client.get('/')
    assert resp.status_code in (200, 302)

    # Test authenticated endpoint without header
    resp = client.get('/test-auth-login')
    assert resp.status_code == 401

    # Test authenticated endpoint with header
    ext_data = {
        'scopes': ['project/test/*', ],
    }
    client_id = 'test/user@mozilla.com'
    header = backend_common.testing.build_header(client_id, ext_data)
    resp = client.get('/test-auth-login', headers=[('Authorization', header)])
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert data['auth']
    assert data['user'] == client_id
    assert data['scopes'] == ext_data['scopes']


def test_scopes_invalid(client):
    '''
    Test the Taskcluster required scopes
    '''

    import backend_common.testing

    client_id = 'test/user@mozilla.com'

    # Missing a scope to validate test
    ext_data = {
        'scopes': ['project/test/A', 'project/test/C', ],
    }
    header = backend_common.testing.build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes', headers=[('Authorization', header)])
    assert resp.status_code == 401


def test_scopes_user(client):
    '''
    Test the Taskcluster required scopes
    '''

    import backend_common.testing

    client_id = 'test/user@mozilla.com'
    # Validate with user scopes
    ext_data = {
        'scopes': ['project/test/A', 'project/test/B', ],
    }
    header = backend_common.testing.build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes',
                      headers=[('Authorization', header)])
    assert resp.status_code == 200
    assert resp.data == b'Your scopes are ok.'


def test_scopes_admin(client):
    '''
    Test the Taskcluster required scopes
    '''

    import backend_common.testing

    client_id = 'test/user@mozilla.com'

    # Validate with admin scopes
    ext_data = {
        'scopes': ['project/another/*', 'project/test-admin/*']
    }
    header = backend_common.testing.build_header(client_id, ext_data)
    resp = client.get('/test-auth-scopes', headers=[('Authorization', header)])
    assert resp.status_code == 200
    assert resp.data == b'Your scopes are ok.'


def test_auth0_access_token(client):
    '''
    Test the validation of an access_token using the auth0 userinfo endpoint
    '''
    resp = client.get('/test-auth0-userinfo',
                      query_string={'access_token': 'abcdef123456'})
    assert resp.status_code == 200
    # side effect of the auth
    assert 'userinfo' in flask.g
    assert flask.g.get('userinfo').get('email') == 'lmoran@mozilla.com'


def test_auth0_access_token_invalid(client):
    '''
    Test the validation of an access_token using the auth0 userinfo endpoint
    '''
    resp = client.get('/test-auth0-userinfo',
                      query_string={'access_token': 'badtoken'})
    assert resp.status_code == 401
    assert json.loads(str(resp.data, 'utf-8')) == {'error': 'invalid_token', 'error_description': 'Unauthorized'}
