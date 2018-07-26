# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools

import requests

PHABRICATOR_API_URL_TEMPLATE = 'https://phabricator.services.mozilla.com/api/{}'
HGMO_JSON_REV_URL_TEMPLATE = 'https://hg.mozilla.org/mozilla-central/json-rev/{}'


@functools.lru_cache(maxsize=2048)
def _revision_exists_on_central(revision):
    url = HGMO_JSON_REV_URL_TEMPLATE.format(revision)
    return requests.get(url).ok


def get_base_revision(phabricator_token, revision_phid):
    '''
    Searches for the most recent base revision that is available on
    https://hg.mozilla.org/mozilla-central, starting from a revision PHID.
    '''
    data = {
        'api.token': phabricator_token,
        'constraints[revisionPHIDs][0]': revision_phid,
    }
    headers = {
        'Accept': 'application/json',
    }
    response = requests.post(PHABRICATOR_API_URL_TEMPLATE.format('differential.diff.search'),
                             data=data,
                             headers=headers)
    j = response.json()
    if j.get('error_code') or j.get('error_info'):
        raise Exception('{error_code}: {error_info}'.format(**j))

    data = j['result']['data']
    data.sort(key=lambda x: x['id'], reverse=True)

    for rev_data in data:
        for field in rev_data['fields']['refs']:
            if field['type'] == 'base':
                revision = field['identifier']
                if _revision_exists_on_central(revision):
                    return revision
