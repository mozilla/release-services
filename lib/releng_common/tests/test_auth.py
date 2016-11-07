from releng_common.auth import Auth, AnonymousUser, TaskclusterUser
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
        user = TaskclusterUser({'clientId' : '', 'scopes' : None})
