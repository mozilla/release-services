from releng_common.mocks import build_header
import json


def _user_header():
    """"
    Helper to build an Hawk header
    for a Shipit dashboard user
    """
    client_id = 'test/shipit-user@mozilla.com'
    ext_data = {
        'scopes': [
            'project:shipit:user',
            'project:shipit:analysis/use',
            'project:shipit:bugzilla',
        ]
    }
    return build_header(client_id, ext_data)


def test_list_analysis_invalid(client):
    """
    List available analysis through api
    """

    # No header : Should fail
    resp = client.get('/analysis')
    assert resp.status_code == 401


def test_list_analysis_valid(client):
    """
    List available analysis through api
    """
    resp = client.get('/analysis', headers=[('Authorization', _user_header())])
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert len(data) == 1
    analysis = data[0]
    assert analysis['id'] == 1
    assert analysis['name'] == 'Analysis Test A'
    assert analysis['parameters'] == 'bugzilla=test'
    assert analysis['bugs'] == []


def test_fetch_analysis(client):
    """
    Fetch detailled analysis, with bugs
    """
    resp = client.get('/analysis/1', headers=[('Authorization', _user_header())])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['name'] == 'Analysis Test A'
    assert analysis['parameters'] == 'bugzilla=test'
    assert analysis['bugs'] == []  # no bugs yet.
