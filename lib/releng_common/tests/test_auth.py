from releng_common.auth import AnonymousUser, TaskclusterUser
import responses
import pytest


def test_anonymous():
    """
    Test AnonymousUser instances
    """

    user = AnonymousUser()

    # Test base
    assert user.get_id() == 'anonymous:'
    assert user.get_permissions() == set()
    assert user.permissions == set()
    assert not user.is_active
    assert user.is_anonymous


def test_taskcluster_user():
    """
    Test TasklusterUser instances
    """

    credentials = {
        'clientId': 'test/user@mozilla.com',
        'scopes': ['project:test:*', ]
    }
    user = TaskclusterUser(credentials)

    # Test base
    assert user.get_id() == credentials['clientId']
    assert user.get_permissions() == credentials['scopes']
    assert user.permissions == credentials['scopes']
    assert user.is_active
    assert not user.is_anonymous

    # Test invalid input
    with pytest.raises(AssertionError):
        user = TaskclusterUser({})
    with pytest.raises(AssertionError):
        user = TaskclusterUser({'clientId': '', 'scopes': None})


@responses.activate
def test_auth(app, client):
    """
    Test the Taskcluster authentication
    """
    assert app.debug

    # Test non authenticated endpoint
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'OK' in resp.data

    # Test authenticated endpoint
    resp = client.get('/test-login')
    assert resp.status_code == 401
    # TODO: use a real hawk header
    resp = client.get('/test-login', headers=[('Authorization', 'Hawk plop')])
    assert resp.status_code == 200
    assert resp.data == b'Authenticated'
