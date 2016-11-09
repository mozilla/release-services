from releng_common.mocks import build_header
import json


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

    # Use valid scopes to list analysis
    client_id = 'test/shipit-user@mozilla.com'
    ext_data = {
        'scopes': [
            'project:shipit:user',
            'project:shipit:analysis/use',
            'project:shipit:bugzilla',
        ]
    }
    header = build_header(client_id, ext_data)

    resp = client.get('/analysis', headers=[('Authorization', header)])
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert len(data) == 0

    # In memory sqlite does not have any analysis
    # assert len(data) == 4
    # all_analysis = {a['id']: a['name'] for a in data}
    # assert all_analysis[1].startswith('Aurora')
    # assert all_analysis[2].startswith('Beta')
    # assert all_analysis[3].startswith('Release')
    # assert all_analysis[4].startswith('Esr')
