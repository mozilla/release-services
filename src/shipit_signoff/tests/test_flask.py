# -*- coding: utf-8 -*-

import json
import backend_common.auth0
import backend_common.testing
from unittest.mock import patch


UID = '1'
INVALID_UID = '1234'

TEST_STEP = {
    'uid': UID,
    'policy': {'method': 'local', 'definition': [{'avengers': 1, 'xmen': 1}]},
    'parameters': {'test': 1},
}

TEST_STEP_SMALL = {
    'uid': UID,
    'policy': {'method': 'local', 'definition': [{'avengers': 1}]},
    'parameters': {'test': 1},
}


GOODHEADERS = {
    'Authorization': 'Bearer goodtoken'
}

BADHEADERS = {
    'Authorization': 'Bearer badtoken'
}


def mocked_getinfo(fields, access_token):
    if access_token == 'goodtoken':
        return backend_common.testing.AUTH0_DUMMY_USERINFO
    else:
        return b'Unauthorized'


def test_login(client):
    # Can't follow the redirect and mock the login, since flask's test client
    # can't be redirected away from the application under test
    resp = client.get('/login',
                      query_string={'callback_url': '/step'})
    assert resp.status_code == 302


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation(client):
    resp = client.put('/step/{}'.format(UID),
                      content_type='application/json',
                      data=json.dumps(TEST_STEP),
                      headers=GOODHEADERS)
    assert resp.status_code == 200


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation_bad_token(client):
    resp = client.put('/step/{}'.format(UID),
                      content_type='application/json',
                      data=json.dumps(TEST_STEP),
                      headers=BADHEADERS)
    assert resp.status_code == 401


def test_get_missing_step(client):
    resp = client.get('/step/{}'.format(INVALID_UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 404


def test_get_present_step(client):
    resp = client.get('/step/{}'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))

    # doesn't return the parameters at the moment, so can't do:
    # assert data == TEST_STEP

    assert 'policy' in data
    assert 'method' in data['policy']
    assert data['policy']['method'] == 'local'


def test_get_step_status(client):
    resp = client.get('/step/{}/status'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))
    assert data['state'] == 'running'
    assert data['uid'] == UID
    assert 'message' in data
    assert 'created' in data


def test_get_missing_step_status(client):
    resp = client.get('/step/{}/status'.format(INVALID_UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 404


def test_delete_step(client):
    resp = client.delete('/step/{}'.format(UID),
                         headers=GOODHEADERS)
    assert resp.status_code == 200


def test_delete_missing_step(client):
    resp = client.delete('/step/{}'.format(INVALID_UID),
                         headers=GOODHEADERS)
    assert resp.status_code == 404


def test_delete_step_bad_token(client):
    resp = client.delete('/step/{}'.format(UID),
                         headers=BADHEADERS)
    assert resp.status_code == 401


def test_step_list(client):
    '''
    List available analysis through api
    '''
    resp = client.get('/step',
                      headers=GOODHEADERS)
    assert resp.status_code == 200


def setup_step(func):
    '''
    Prepopulate the testing database.

    Can't use a fixture because it cancels the @patch to user_getinfo
    '''
    def decorator(client, *args, **kwargs):
        client.put('/step/{}'.format(UID),
                   content_type='application/json',
                   data=json.dumps(TEST_STEP),
                   headers=GOODHEADERS)
        func(client)
        client.delete('/step/{}'.format(UID),
                      headers=GOODHEADERS)
    return decorator


def setup_step_small(func):
    '''
    Prepopulate the testing database.

    Can't use a fixture because it cancels the @patch to user_getinfo
    '''
    def decorator(client, *args, **kwargs):
        client.put('/step/{}'.format(UID),
                   content_type='application/json',
                   data=json.dumps(TEST_STEP_SMALL),
                   headers=GOODHEADERS)
        func(client)
        client.delete('/step/{}'.format(UID),
                      headers=GOODHEADERS)
    return decorator


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off(client):
    data = {
        'group': 'avengers',
    }
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 200


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_sign_off_missing_data(client):
    resp = client.put('/step/{}/sign'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 400


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_unauthorized(client):
    data = {
        'group': 'invalidgroup',
    }
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 403


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_sign_off_missing_step(client):
    data = {
        'group': 'releng',
    }
    resp = client.put('/step/{}/sign'.format(INVALID_UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 404


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_sign_off_bad_token(client):
    data = {
        'group': 'releng',
    }
    resp = client.put('/step/{}/sign'.format(INVALID_UID),
                      content_type='application/json',
                      headers=BADHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 401


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_signing_twice(client):
    data = {
        'group': 'avengers',
    }
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 200
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 409


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_deletion(client):
    data = {
        'group': 'avengers',
    }
    # First sign the step
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))

    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))

    assert resp.status_code == 200


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_deletion_without_signing(client):
    data = {
        'group': 'avengers',
    }

    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))
    assert resp.status_code == 409


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_deletion_missing_step(client):
    data = {
        'group': 'avengers',
    }
    resp = client.delete('/step/{}/sign'.format(INVALID_UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))
    assert resp.status_code == 404


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_deletion_no_signatures(client):
    data = {
        'group': 'invalidgroup',
    }
    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))
    assert resp.status_code == 403


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step
def test_sign_off_deletion_unauthorized(client):
    data = {
        'group': 'avengers',
    }
    # First sign the step
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))

    data = {
        'group': 'fantastic4',
    }
    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))
    assert resp.status_code == 403


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
@setup_step_small
def test_sign_off_deletion_completed(client):
    '''Try to delete a step when it has been fully signed off.'''
    data = {
        'group': 'avengers',
    }
    # First sign the step
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))

    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))
    assert resp.status_code == 409


# delete a step when you haven't signed it

# get step status when fully signed.
