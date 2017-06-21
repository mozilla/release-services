# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import urllib.parse
import json


def assert_query_strings(x, y):
    '''
    Helper to compare Query strings
    '''
    x = urllib.parse.parse_qs(x)
    y = urllib.parse.parse_qs(y)
    assert x == y


def test_list_analysis_invalid(client):
    '''
    List available analysis through api
    '''

    # No header : Should fail
    resp = client.get(
        '/analysis',
    )
    assert resp.status_code == 401


def test_list_analysis_valid(client, bugs, header_user):
    '''
    List available analysis through api
    '''
    resp = client.get(
        '/analysis',
        headers=[
            ('Authorization', header_user),
        ],
    )
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert len(data) == 2
    analysis = data[0]
    assert analysis['id'] == 1
    assert analysis['name'] == 'Dev'
    assert_query_strings(
        analysis['parameters'],
        'j1=OR&o5=substring&f12=CP&o3=substring&f0=OP&v3=approval-mozilla-dev%3F&j9=OR&o2=substring&f10=requestees.login_name&f11=CP&f4=flagtypes.name&f2=flagtypes.name&f9=OP&f3=flagtypes.name&query_format=advanced&f7=CP&f1=OP&f8=OP&f6=CP&known_name=approval-mozilla-dev&query_based_on=approval-mozilla-dev&o4=substring&f5=flagtypes.name&o10=substring'  # noqa
    )
    assert analysis['bugs'] == []


def test_fetch_analysis(client, bugs, header_user):
    '''
    Fetch detailled analysis, with bugs
    '''
    resp = client.get(
        '/analysis/1',
        headers=[
            ('Authorization', header_user),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['version'] == 1
    assert analysis['name'] == 'Dev'
    assert_query_strings(
        analysis['parameters'],
        'j1=OR&o5=substring&f12=CP&o3=substring&f0=OP&v3=approval-mozilla-dev%3F&j9=OR&o2=substring&f10=requestees.login_name&f11=CP&f4=flagtypes.name&f2=flagtypes.name&f9=OP&f3=flagtypes.name&query_format=advanced&f7=CP&f1=OP&f8=OP&f6=CP&known_name=approval-mozilla-dev&query_based_on=approval-mozilla-dev&o4=substring&f5=flagtypes.name&o10=substring'  # noqa
    )
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


def test_analysis_query_strings():
    '''
    Check Bugzilla parameters building
    '''
    from shipit_uplift.models import BugAnalysis

    assert_query_strings(
        BugAnalysis(name='aurora', version=52).build_parameters(),
        'o5=substring&j9=OR&o2=substring&f12=CP&o4=substring&known_name=approval-mozilla-aurora&f10=requestees.login_name&f1=OP&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-aurora%3F&query_based_on=approval-mozilla-aurora&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&j1=OR&f3=flagtypes.name&f2=flagtypes.name&f11=CP&f5=flagtypes.name&f6=CP&f7=CP'  # noqa
    )
    assert_query_strings(
        BugAnalysis(name='beta', version=51).build_parameters(),
        'o5=substring&f10=requestees.login_name&f1=OP&j9=OR&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-beta%3F&query_based_on=approval-mozilla-beta&o2=substring&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&f12=CP&j1=OR&f3=flagtypes.name&f2=flagtypes.name&o4=substring&f11=CP&f5=flagtypes.name&f6=CP&f7=CP&known_name=approval-mozilla-beta'  # noqa
    )
    assert_query_strings(
        BugAnalysis(name='release', version=50).build_parameters(),
        'o5=substring&j9=OR&o2=substring&f12=CP&o4=substring&known_name=approval-mozilla-release&f10=requestees.login_name&f1=OP&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-release%3F&query_based_on=approval-mozilla-release&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&j1=OR&f3=flagtypes.name&f2=flagtypes.name&f11=CP&f5=flagtypes.name&f6=CP&f7=CP'  # noqa
    )
    assert_query_strings(
        BugAnalysis(name='esr', version=45).build_parameters(),
        'o5=substring&f10=requestees.login_name&f1=OP&j9=OR&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-esr45%3F&query_based_on=approval-esr45&o2=substring&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&f12=CP&j1=OR&f3=flagtypes.name&f2=flagtypes.name&o4=substring&f11=CP&f5=flagtypes.name&f6=CP&f7=CP&known_name=approval-esr45'  # noqa
    )


def test_update_analysis(client, bugs, header_bot, header_user):
    '''
    Update analysis version
    '''
    url = '/analysis/1'

    # Check analysis has version 1 initially
    resp = client.get(
        url,
        headers=[
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['version'] == 1
    assert analysis['name'] == 'Dev'

    # Update to version 2
    data = {
        'version': 2,
    }

    # Only bot has access to the update endpoint
    resp = client.put(
        url,
        data=json.dumps(data),
        headers=[
            ('Authorization', header_user),
            ('Content-Type', 'application/json'),
        ],
    )
    assert resp.status_code == 401

    # Update as bot
    resp = client.put(
        url,
        data=json.dumps(data),
        headers=[
            ('Authorization', header_bot),
            ('Content-Type', 'application/json'),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['version'] == 2
    assert analysis['name'] == 'Dev'

    # Check analysis has version 2 now
    # Accessible by user on GET
    resp = client.get(
        url,
        headers=[
            ('Authorization', header_user),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert analysis['id'] == 1
    assert analysis['version'] == 2
    assert analysis['name'] == 'Dev'


def test_create_bug(client, bugs, header_bot):
    '''
    Create a new bug in analysis
    '''
    # Check we have 3 bugs
    resp = client.get(
        '/analysis/1',
        headers=[
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 3

    # Create a new bug
    data = {
        'bugzilla_id': 12345,
        'analysis': [1, 2, ],
        'payload_hash': 'deadbeef12345',
        'payload': json.load(open('tests/fixtures/payload_12345.json')),
    }
    resp = client.post(
        '/bugs',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    bug_created = json.loads(resp.data.decode('utf-8'))
    assert bug_created == {
        'bugzilla_id': 12345,
        'changes_size': 0,
        'component': 'Reading List',
        'product': 'Firefox',
        'status': 'RESOLVED',
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
        'flags_generic': {'firefox-backlog': '+',
                          'qe-verify': '---'},
        'id': 4,
        'keywords': ['test'],
        'landings': {'aurora': 'Fri, 10 Apr 2015 17:06:41 GMT',
                     'nightly': 'Wed, 08 Apr 2015 16:43:32 GMT'},
        'patches': {'41a0c9bc40df': {'changes_add': 51,
                                     'changes_del': 9,
                                     'changes_size': 162,
                                     'languages': ['Python'],
                                     'merge': {
                                        'aurora': True,
                                        'beta': False,
                                     },
                                     'source': 'mercurial',
                                     'url': 'https://hg.mozilla.org/mozilla-central/rev/41a0c9bc40df'}},  # noqa
        'summary': 'Desktop reading list sync module should batch its POST /batch '  # noqa
                   'requests',
        'uplift': {'comment': '<div>Comment</div>', 'id': 10138846},
        'url': 'https://bugzilla-dev.allizom.org/1151077',
        'versions': {}}

    # Check we now have 4 bugs
    resp = client.get(
        '/analysis/1',
        headers=[
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200
    analysis = json.loads(resp.data.decode('utf-8'))
    assert len(analysis['bugs']) == 4


def test_deprecating_bug(client, bugs, header_bot):
    '''
    Deprecate a bug from an analysis
    '''
    def in_analysis(bugzilla_id, analysis_id):
        # Check a bug is in an analysis
        url = '/analysis/{}'.format(analysis_id)
        resp = client.get(
            url,
            headers=[
                ('Authorization', header_bot),
            ],
        )
        assert resp.status_code == 200
        analysis = json.loads(resp.data.decode('utf-8'))
        return bugzilla_id in [b['bugzilla_id'] for b in analysis['bugs']]

    # We should have bug 12345 on analysis 1 & 2
    assert in_analysis(12345, 1)
    assert in_analysis(12345, 2)

    # Remove bug from analysis 2
    data = {
        'bugzilla_id': 12345,
        'analysis': [1, ],
        'payload_hash': 'deadbeef12345',
        'payload': json.load(open('tests/fixtures/payload_12345.json')),
        'versions': {},
    }
    resp = client.post(
        '/bugs',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_bot),
        ],
    )
    assert resp.status_code == 200

    # We should have bug 12345 in analysis 1 only
    assert in_analysis(12345, 1)
    assert not in_analysis(12345, 2)


def test_delete_bug(client, bugs, header_bot):
    '''Delete a bug in an analysis.
    '''
    # Check we have 4 bugs
    resp = client.get(
        '/analysis/1',
        headers=[
            ('Authorization', header_bot),
        ],
    )

    assert resp.status_code == 200

    analysis = json.loads(resp.data.decode('utf-8'))

    assert len(analysis['bugs']) == 4

    # Delete created bug 12345
    resp = client.delete(
        '/bugs/12345',
        headers=[
            ('Authorization', header_bot),
        ],
    )

    assert resp.status_code == 200

    # Check we now have 3 bugs
    resp = client.get(
        '/analysis/1',
        headers=[
            ('Authorization', header_bot),
        ],
    )

    assert resp.status_code == 200

    analysis = json.loads(resp.data.decode('utf-8'))

    assert len(analysis['bugs']) == 3

    # Check bug is removed
    assert 12345 not in [b['bugzilla_id'] for b in analysis['bugs']]


def test_update_bug_flags(client, bugs, header_user):
    '''Update tracking flags for a bug.
    '''

    data = [{
        'target': 'bug',
        'bugzilla_id': 1139560,
        'changes': {
            'cf_status_firefox38': {
                'removed': 'affected',
                'added': 'fixed',
            },
            'cf_tracking_firefox40': {
                'removed': '---',
                'added': '+',
            },
            'flagtypes.name': {
                'removed': '',
                'added': 'qe-verify+',
            },
        }
    }]

    resp = client.put(
        '/bugs/1139560',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_user),
        ],
    )

    assert resp.status_code == 200

    bug = json.loads(resp.data.decode('utf-8'))

    assert bug['flags_generic'] == {
        'in-testsuite': '+',
        'qe-verify': '+',
    }

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
    '''Update attachment for a bug.
    '''
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

    resp = client.put(
        '/bugs/1139560',
        data=json.dumps(data),
        headers=[
            ('Content-Type', 'application/json'),
            ('Authorization', header_user),
        ],
    )

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
