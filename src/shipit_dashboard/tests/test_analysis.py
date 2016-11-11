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


def test_list_analysis_valid(client, bugs):
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


def test_fetch_analysis(client, bugs):
    """
    Fetch detailled analysis, with bugs
    """
    resp = client.get('/analysis/1', headers=[
        ('Authorization', _user_header()),
    ])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['name'] == 'Analysis Test A'
    assert analysis['parameters'] == 'bugzilla=test'
    assert len(analysis['bugs']) == 3

    bugs = {b['bugzilla_id']: b for b in analysis['bugs']}
    bug = bugs[1139560]
    assert bug['summary'] == '`srcset` parser doesn’t adhere to the spec'
    assert bug['keywords'] == ['dev-doc-needed', 'regression']
    assert bug['landings'] == {
        'aurora': 'Fri, 10 Apr 2015 23:42:04 GMT',
        'nightly': 'Fri, 10 Apr 2015 02:50:46 GMT'
    }
    assert bug['url'] == 'https://bugzilla-dev.allizom.org/1139560'
    assert bug['versions'] == {
        'aurora +': {
            'attachments': ['8590815'],
            'name': 'approval-mozilla-aurora',
            'status': '+'
        },
        'beta ?': {
            'attachments': ['8590815'],
            'name': 'approval-mozilla-beta',
            'status': '?'
        }
    }
    assert bug['uplift']['id'] == 10141284
    assert bug['flags_status'] == {
        'firefox37': '---',
        'firefox38': 'affected',
        'firefox39': 'fixed',
        'firefox40': 'fixed',
        'firefox_esr31': '---',
        'firefox_esr38': '---',
    }
    assert bug['flags_tracking'] == {
        'firefox37': '---',
        'firefox38': '+',
        'firefox39': '+',
        'firefox40': '---',
        'firefox_esr31': '---',
        'firefox_esr38': '---',
        'firefox_relnote': '---',
    }
