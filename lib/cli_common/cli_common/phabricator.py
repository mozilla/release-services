# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import logging
from urllib.parse import urlparse

import requests

HGMO_JSON_REV_URL_TEMPLATE = 'https://hg.mozilla.org/mozilla-central/json-rev/{}'
MOZILLA_PHABRICATOR_PROD = 'https://phabricator.services.mozilla.com/api/'


logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=2048)
def revision_exists_on_central(revision):
    url = HGMO_JSON_REV_URL_TEMPLATE.format(revision)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.ok


class ConduitError(Exception):
    '''
    Exception to be raised when Phabricator returns an error response.
    '''
    def __init__(self, msg, error_code=None, error_info=None):
        super(ConduitError, self).__init__(msg)
        self.error_code = error_code
        self.error_info = error_info
        logger.warn('Conduit API error {} : {}'.format(
            self.error_code,
            self.error_info or 'unknown'
        ))

    @classmethod
    def raise_if_error(cls, response_body):
        '''
        Raise a ConduitError if the provided response_body was an error.
        '''
        if response_body['error_code'] is not None:
            raise cls(
                response_body.get('error_info'),
                error_code=response_body.get('error_code'),
                error_info=response_body.get('error_info')
            )


class PhabricatorAPI(object):
    '''
    Phabricator Rest API client
    '''
    def __init__(self, api_key, url=MOZILLA_PHABRICATOR_PROD):
        self.api_key = api_key
        self.url = url
        assert self.url.endswith('/api/'), \
            'Phabricator API must end with /api/'

        # Test authentication
        self.user = self.request('user.whoami')
        logger.info('Authenticated on {} as {}'.format(self.url, self.user['realName']))

    @property
    def hostname(self):
        parts = urlparse(self.url)
        return parts.netloc

    def search_diffs(self, diff_phid=None, revision_phid=None):
        '''
        Find details of differential diffs from a Differential diff or revision
        Multiple diffs can be returned (when using revision_phid)
        '''
        assert (diff_phid is not None) ^ (revision_phid is not None), \
            'Provide a diff_phid XOR revision_phid'

        constraints = {}
        if diff_phid is not None:
            constraints['phids'] = [diff_phid, ]
        if revision_phid is not None:
            constraints['revisionPHIDs'] = [revision_phid, ]
        out = self.request('differential.diff.search', constraints=constraints)

        def _clean(diff):

            # Make all fields easily accessible
            if 'fields' in diff and isinstance(diff['fields'], dict):
                diff.update(diff['fields'])
                del diff['fields']

            # Lookup base revision in refs
            diff['refs'] = {
                ref['type']: ref
                for ref in diff['refs']
            }
            diff['baseRevision'] = diff['refs']['base']['identifier']

            return diff

        return list(map(_clean, out['data']))

    def load_raw_diff(self, diff_id):
        '''
        Load the raw diff content
        '''
        return self.request(
            'differential.getrawdiff',
            diffID=diff_id,
        )

    def load_revision(self, phid):
        '''
        Find details of a differential revision
        '''
        out = self.request(
            'differential.revision.search',
            constraints={
                'phids': [phid, ],
            },
        )

        data = out['data']
        assert len(data) == 1, \
            'Revision not found'
        return data[0]

    def list_comments(self, revision_phid):
        '''
        List and format existing inline comments for a revision
        '''
        transactions = self.request(
            'transaction.search',
            objectIdentifier=revision_phid,
        )
        return [
            {

                'diffID': transaction['fields']['diff']['id'],
                'filePath': transaction['fields']['path'],
                'lineNumber': transaction['fields']['line'],
                'lineLength': transaction['fields']['length'],
                'content': comment['content']['raw'],

            }
            for transaction in transactions['data']
            for comment in transaction['comments']
            if transaction['type'] == 'inline' and transaction['authorPHID'] == self.user['phid']
        ]

    def comment(self, revision_id, message):
        '''
        Comment on a Differential revision
        Using a frozen method as new transactions does not
        seem to support inlines publication
        '''
        return self.request(
            'differential.createcomment',
            revision_id=revision_id,
            message=message,
            attach_inlines=1,
        )

    def request(self, path, **payload):
        '''
        Send a request to Phabricator API
        '''

        def flatten_params(params):
            '''
            Flatten nested objects and lists.
            Phabricator requires query data in a application/x-www-form-urlencoded
            format, so we need to flatten our params dictionary.
            '''
            assert isinstance(params, dict)
            flat = {}
            remaining = list(params.items())

            # Run a depth-ish first search building the parameter name
            # as we traverse the tree.
            while remaining:
                key, o = remaining.pop()
                if isinstance(o, dict):
                    gen = o.items()
                elif isinstance(o, list):
                    gen = enumerate(o)
                else:
                    flat[key] = o
                    continue

                remaining.extend(('{}[{}]'.format(key, k), v) for k, v in gen)

            return flat

        # Add api token to payload
        payload['api.token'] = self.api_key

        # Run POST request on api
        response = requests.post(
            self.url + path,
            data=flatten_params(payload),
        )

        # Check response
        data = response.json()
        assert response.ok
        assert 'error_code' in data
        ConduitError.raise_if_error(data)

        # Outputs result
        assert 'result' in data
        return data['result']
