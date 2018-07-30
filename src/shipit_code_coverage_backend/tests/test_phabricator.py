# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import responses

URL_TEMPLATE = '/phabricator/base_revision_from_phid/{}'


@responses.activate
def test_phabricator_get_revision_from_phid_api_hit(client, phabricator_responses,
                                                    hgmo_phab_rev_responses):
    REVISION_PHID = 'PHID-DREV-esv6jbcptwuju667eiyx'
    resp = client.get(URL_TEMPLATE.format(REVISION_PHID))
    assert resp.status_code == 200
    assert resp.json == {'revision': '2ed1506d1dc7db3d70a3feed95f1456bce05bbee'}


@responses.activate
def test_phabricator_get_revision_from_phid_api_miss(client, phabricator_responses,
                                                     hgmo_phab_rev_responses):
    REVISION_PHID = 'PHID-DREV-xxxxxxxxxxxxxxxxxxxx'
    resp = client.get(URL_TEMPLATE.format(REVISION_PHID))
    assert resp.status_code == 404
    assert 'not found' in resp.json['error']


@responses.activate
def test_phabricator_get_revision_from_phid_api_bad_token(client, phabricator_responses,
                                                          mock_secrets_bad_phabricator_token):
    REVISION_PHID = 'PHID-DREV-esv6jbcptwuju667eiyx'
    resp = client.get(URL_TEMPLATE.format(REVISION_PHID))
    assert resp.status_code == 500
    assert 'INVALID-AUTH' in resp.json['error']
