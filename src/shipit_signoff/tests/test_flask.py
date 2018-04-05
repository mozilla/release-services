# -*- coding: utf-8 -*-

import json
import pickle
from unittest.mock import patch

import backend_common.auth0
import backend_common.testing
from backend_common.db import db
from shipit_signoff.api import is_user_in_group
from shipit_signoff.models import SigningStatus
from shipit_signoff.models import SignoffStep

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

TEST_STEP_BALROG = {
    'uid': UID,
    'policy': {'method': 'balrog', 'definition': {'sc_id': 23, 'object': 'rules'}},
    'parameters': {},
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


def mocked_current_user_roles(*args, **kwargs):
    return ['avengers', 'x_men']


mocked_balrog_signoff_status_waiting = ({}, {'avengers': 1})
mocked_balrog_signoff_status_completed = ({'capt': 'avengers'}, {'avengers': 1})


@patch('shipit_signoff.api.get_current_user_roles', new=mocked_current_user_roles)
def test_is_user_in_group_balrog():
    assert is_user_in_group('x_men', method='balrog') is True


def test_login(client):
    # Can't follow the redirect and mock the login, since flask's test client
    # can't be redirected away from the application under test
    resp = client.get('/login',
                      query_string={'callback_url': '/step'})
    assert resp.status_code == 302


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


def setup_step_balrog(func):
    '''
    Prepopulate the testing database.

    Can't use a fixture because it cancels the @patch to user_getinfo
    '''
    def decorator(client, *args, **kwargs):
        step = SignoffStep()
        step.uid = UID
        step.policy = pickle.dumps(TEST_STEP_BALROG['policy'])
        step.state = 'running'
        db.session.add(step)
        db.session.commit()
        func(client)
    return decorator


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation(client):
    resp = client.put('/step/{}'.format(UID),
                      content_type='application/json',
                      data=json.dumps(TEST_STEP),
                      headers=GOODHEADERS)
    assert resp.status_code == 200


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation_balrog(client):
    with patch('shipit_signoff.balrog.get_signoff_status') as status_mock:
        status_mock.return_value = mocked_balrog_signoff_status_waiting
        resp = client.put('/step/{}'.format(UID),
                          content_type='application/json',
                          data=json.dumps(TEST_STEP_BALROG),
                          headers=GOODHEADERS)
        assert resp.status_code == 200
        assert status_mock.call_count == 1


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation_balrog_already_completed(client):
    with patch('shipit_signoff.balrog.get_signoff_status') as status_mock:
        status_mock.return_value = mocked_balrog_signoff_status_completed
        resp = client.put('/step/{}'.format(UID),
                          content_type='application/json',
                          data=json.dumps(TEST_STEP_BALROG),
                          headers=GOODHEADERS)
        assert resp.status_code == 200
        assert status_mock.call_count == 1
        row = db.session.query(SignoffStep).filter(SignoffStep.uid == UID).one()
        assert row.state == SigningStatus.completed


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation_bad_token(client):
    resp = client.put('/step/{}'.format(UID),
                      content_type='application/json',
                      data=json.dumps(TEST_STEP),
                      headers=BADHEADERS)
    assert resp.status_code == 401


@patch('backend_common.auth0.auth0.user_getinfo', new=mocked_getinfo)
def test_step_creation_bad_method(client):
    step = {
        'uid': UID,
        'policy': {'method': 'fake', 'definition': [{'avergers': 1}]},
        'parameters': {},
    }
    resp = client.put('/step/{}'.format(UID),
                      content_type='application/json',
                      data=json.dumps(step),
                      headers=GOODHEADERS)
    assert resp.status_code == 400


def test_get_missing_step(client):
    resp = client.get('/step/{}'.format(INVALID_UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 404


@setup_step
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


@setup_step_balrog
def test_get_present_step_balrog(client):
    resp = client.get('/step/{}'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))

    # doesn't return the parameters at the moment, so can't do:
    # assert data == TEST_STEP

    assert 'policy' in data
    assert 'method' in data['policy']
    assert data['policy']['method'] == 'balrog'


@setup_step
def test_get_step_status(client):
    resp = client.get('/step/{}/status'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))
    assert data['state'] == 'running'
    assert data['uid'] == UID
    assert 'message' in data
    assert 'created' in data


@setup_step_balrog
@patch('shipit_signoff.balrog.get_signoff_status')
def test_get_step_status_balrog_no_change(client, status_mock):
    status_mock.return_value = mocked_balrog_signoff_status_waiting
    resp = client.get('/step/{}/status'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))
    assert data['state'] == 'running'
    assert data['uid'] == UID
    assert 'message' in data
    assert 'created' in data
    assert status_mock.call_count == 1


@setup_step_balrog
@patch('shipit_signoff.balrog.get_signoff_status')
def test_get_step_status_balrog_completed(client, status_mock):
    status_mock.return_value = mocked_balrog_signoff_status_completed
    resp = client.get('/step/{}/status'.format(UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 200
    data = json.loads(str(resp.data, 'utf-8'))
    assert data['state'] == 'completed'
    assert data['uid'] == UID
    assert 'message' in data
    assert 'created' in data
    assert status_mock.call_count == 1
    row = db.session.query(SignoffStep).filter(SignoffStep.uid == UID).one()
    assert row.state == SigningStatus.completed


def test_get_missing_step_status(client):
    resp = client.get('/step/{}/status'.format(INVALID_UID),
                      headers=GOODHEADERS)
    assert resp.status_code == 404


@setup_step
def test_delete_step(client):
    resp = client.delete('/step/{}'.format(UID),
                         headers=GOODHEADERS)
    assert resp.status_code == 200


@setup_step_balrog
def test_delete_step_balrog(client):
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
    # TODO: add a few steps


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
@patch('shipit_signoff.api.get_current_user_roles', new=mocked_current_user_roles)
@setup_step_balrog
def test_sign_off_balrog(client):
    data = {
        'group': 'avengers',
    }
    resp = client.put('/step/{}/sign'.format(UID),
                      content_type='application/json',
                      headers=GOODHEADERS,
                      data=json.dumps(data))
    assert resp.status_code == 307
    assert resp.headers['Location'] == 'https://balrog/api/scheduled_changes/rules/23/signoffs'


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
@patch('shipit_signoff.api.get_current_user_roles', new=mocked_current_user_roles)
@setup_step_balrog
def test_sign_off_deletion_balrog(client):
    data = {
        'group': 'avengers',
    }

    resp = client.delete('/step/{}/sign'.format(UID),
                         content_type='application/json',
                         headers=GOODHEADERS,
                         data=json.dumps(data))

    assert resp.status_code == 307
    assert resp.headers['Location'] == 'https://balrog/api/scheduled_changes/rules/23/signoffs'


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
