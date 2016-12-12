import json


def test_list_analysis_invalid(client):
    """
    List available analysis through api
    """

    # No header : Should fail
    resp = client.get('/analysis')
    assert resp.status_code == 401


def test_list_analysis_valid(client, bugs, header_user):
    """
    List available analysis through api
    """
    resp = client.get('/analysis', headers=[
        ('Authorization', header_user),
    ])
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert len(data) == 1
    analysis = data[0]
    assert analysis['id'] == 1
    assert analysis['name'] == 'Analysis Test A'
    assert analysis['parameters'] == 'bugzilla=test'
    assert analysis['bugs'] == []


def test_fetch_analysis(client, bugs, header_user):
    """
    Fetch detailled analysis, with bugs
    """
    resp = client.get('/analysis/1', headers=[
        ('Authorization', header_user),
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


def test_create_bug(client, bugs, header_bot):
    """
    Create a new bug in analysis
    """
    # Check we have 3 bugs
    resp = client.get('/analysis/1', headers=[
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 3

    # Create a new bug
    data = {
        'bugzilla_id': 12345,
        'analysis': [1, ],
        'payload_hash': 'deadbeef12345',
        'payload': {
            "analysis": {
                "landings": {
                    "aurora": "Fri, 10 Apr 2015 17:06:41 GMT",
                    "beta": None,
                    "esr": None,
                    "nightly": "Wed, 08 Apr 2015 16:43:32 GMT",
                    "release": None
                },
                "patches": {
                    "41a0c9bc40df": {
                        "changes_add": 51,
                        "changes_del": 9,
                        "changes_size": 162,
                        "source": "mercurial",
                        "url": "https://hg.mozilla.org/mozilla-central/rev/41a0c9bc40df",  # noqa
                        "languages": ["Python"],
                    }
                },
                "uplift_accepted": False,
                "uplift_comment": {
                    "author": "adw@mozilla.com",
                    "html": "<div>Comment</div>",
                    "id": 10138846,
                    "text": "Comment",
                    "time": "2015-04-09T22:04:10Z"
                }
            },
            "bug": {
                "assigned_to": "adw@mozilla.com",
                "assigned_to_detail": {
                    "email": "adw@mozilla.com",
                    "id": 334927,
                    "name": "adw@mozilla.com",
                    "real_name": "Drew Willcoxon :adw"
                },
                "cc": [
                    "mhammond@mozilla.com",
                ],
                "cf_status_firefox37": "---",
                "cf_status_firefox38": "affected",
                "cf_status_firefox39": "fixed",
                "cf_status_firefox40": "fixed",
                "cf_status_firefox_esr31": "---",
                "cf_status_firefox_esr38": "---",
                "cf_tracking_e10s": "---",
                "cf_tracking_firefox37": "---",
                "cf_tracking_firefox38": "---",
                "cf_tracking_firefox39": "---",
                "cf_tracking_firefox40": "---",
                "cf_tracking_firefox_esr31": "---",
                "cf_tracking_firefox_esr38": "---",
                "cf_tracking_firefox_relnote": "---",
                "component": "Reading List",
                "creation_time": "2015-04-03T21:35:10Z",
                "flags": [
                    {
                        "creation_date": "2015-04-07T00:02:11Z",
                        "id": 1140307,
                        "modification_date": "2015-04-07T00:02:11Z",
                        "name": "firefox-backlog",
                        "setter": "mhammond@mozilla.com",
                        "status": "+",
                        "type_id": 846
                    },
                ],
                "id": 1151077,
                "is_confirmed": True,
                "is_creator_accessible": True,
                "is_open": False,
                "keywords": ["test", ],
                "last_change_time": "2015-04-10T17:06:41Z",
                "platform": "All",
                "priority": "P1",
                "product": "Firefox",
                "resolution": "FIXED",
                "severity": "normal",
                "status": "RESOLVED",
                "summary": "Desktop reading list sync module should batch its POST /batch requests",  # noqa
                "target_milestone": "Firefox 40",
            },
            "url": "https://bugzilla-dev.allizom.org/1151077",
            "users": [
                {
                    "can_login": True,
                    "email": "adw@mozilla.com",
                    "groups": [],
                    "id": 334927,
                    "is_new": False,
                    "last_activity": "2015-04-09T22:58:39Z",
                    "name": "adw@mozilla.com",
                    "real_name": "Drew Willcoxon :adw",
                    "roles": [
                        "creator",
                        "assignee",
                        "uplift_author"
                    ]
                }
            ]
        }
    }
    resp = client.post('/bugs', data=json.dumps(data), headers=[
        ('Content-Type', 'application/json'),
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200
    bug_created = json.loads(resp.data.decode('utf-8'))
    assert bug_created == {
        'bugzilla_id': 12345,
        'changes_size': 0,
        'contributors': [
            {
                'id': 4,
                'avatar': 'https://www.gravatar.com/avatar/fa60148022a230fe1bacc441549b1c66',  # noqa
                'email': 'adw@mozilla.com',
                'name': 'Drew Willcoxon :adw',
                'roles': ['creator', 'assignee', 'uplift_author'],
                'karma': 0,
                'comment_public': '',
            }
        ],
        'flags_status': {'firefox37': '---',
                         'firefox38': 'affected',
                         'firefox39': 'fixed',
                         'firefox40': 'fixed',
                         'firefox_esr31': '---',
                         'firefox_esr38': '---'},
        'flags_tracking': {'firefox37': '---',
                           'firefox38': '---',
                           'firefox39': '---',
                           'firefox40': '---',
                           'firefox_esr31': '---',
                           'firefox_esr38': '---',
                           'firefox_relnote': '---'},
        'id': 4,
        'keywords': ['test'],
        'landings': {'aurora': 'Fri, 10 Apr 2015 17:06:41 GMT',
                     'nightly': 'Wed, 08 Apr 2015 16:43:32 GMT'},
        'patches': {'41a0c9bc40df': {'changes_add': 51,
                                     'changes_del': 9,
                                     'changes_size': 162,
                                     'languages': ['Python'],
                                     'source': 'mercurial',
                                     'url': 'https://hg.mozilla.org/mozilla-central/rev/41a0c9bc40df'}},  # noqa
        'summary': 'Desktop reading list sync module should batch its POST /batch '  # noqa
                   'requests',
        'uplift': {'comment': '<div>Comment</div>', 'id': 10138846},
        'url': 'https://bugzilla-dev.allizom.org/1151077',
        'versions': {}}

    # Check we now have 4 bugs
    resp = client.get('/analysis/1', headers=[
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 4


def test_delete_bug(client, bugs, header_bot):
    """
    Delete a bug in an analysis
    """
    # Check we have 4 bugs
    resp = client.get('/analysis/1', headers=[
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 4

    # Delete created bug 12345
    resp = client.delete('/bugs/12345', headers=[
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200

    # Check we now have 3 bugs
    resp = client.get('/analysis/1', headers=[
        ('Authorization', header_bot),
    ])
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 3

    # Check bug is removed
    assert 12345 not in [b['bugzilla_id'] for b in analysis['bugs']]


def test_update_bug_flags(client, bugs, header_user):
    """
    Update tracking flags for a bug
    """
    data = [{
        'target': 'bug',
        'bugzilla_id': 1139560,
        'changes': {
            'cf_status_firefox38': {
                'remoced': 'affected',
                'added': 'fixed',
            },
            'cf_tracking_firefox40': {
                'remoced': '---',
                'added': '+',
            },
        }
    }]
    resp = client.put('/bugs/1139560', data=json.dumps(data), headers=[
        ('Content-Type', 'application/json'),
        ('Authorization', header_user),
    ])
    assert resp.status_code == 200
    bug = json.loads(resp.data.decode('utf-8'))
    assert bug['flags_status'] == {
        'firefox37': '---',
        'firefox38': 'fixed',
        'firefox39': 'fixed',
        'firefox40': 'fixed',
        'firefox_esr31': '---',
        'firefox_esr38': '---',
    }
    assert bug['flags_tracking'] == {
        'firefox37': '---',
        'firefox38': '+',
        'firefox39': '+',
        'firefox40': '+',
        'firefox_esr31': '---',
        'firefox_esr38': '---',
        'firefox_relnote': '---',
    }


def test_update_bug_attachment(client, bugs, header_user):
    """
    Update attachment for a bug
    """
    data = [{
        'target': 'attachment',
        'bugzilla_id': 8590815,  # attachment id
        'changes': {
            'flagtypes.name': {
                'removed': 'approval-mozilla-beta?, approval-mozilla-aurora+',
                'added': 'approval-mozilla-beta+, approval-mozilla-aurora-',
            },
        }
    }]
    resp = client.put('/bugs/1139560', data=json.dumps(data), headers=[
        ('Content-Type', 'application/json'),
        ('Authorization', header_user),
    ])
    assert resp.status_code == 200
    bug = json.loads(resp.data.decode('utf-8'))
    assert bug['versions'] == {
        'aurora -': {
            'attachments': ['8590815'],
            'name': 'approval-mozilla-aurora',
            'status': '-'
        },
        'beta +': {
            'attachments': ['8590815'],
            'name': 'approval-mozilla-beta',
            'status': '+'
        }
    }
