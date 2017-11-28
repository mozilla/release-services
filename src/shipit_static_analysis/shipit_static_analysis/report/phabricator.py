# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cli_common import log
from shipit_static_analysis.clang import ClangIssue
from shipit_static_analysis.report.base import Reporter
import requests

logger = log.get_logger(__name__)


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


class PhabricatorReporter(Reporter):
    '''
    API connector to report on Phabricator
    '''
    def __init__(self, configuration, *args):
        self.url, self.api_key = self.requires(configuration, 'url', 'api_key')
        assert self.url.endswith('/api/'), \
            'Phabricator API must end with /api/'

        # Create a unique session for all requests
        self.session = requests.Session()
        out = self.request('user.whoami')

        from pprint import pprint
        pprint(out)

    def publish(self, issues, review_request_id, diffset_revision, diff_url):
        '''
        Send an email to administrators
        '''

    def comment(self, revision_id, message):
        '''
        Comment on a revision
        '''
        transactions = [
            {
                'type': 'comment',
                'value': message,
            }
        ]
        out = self.request(
            'diffusion.commit.edit',
            objectIdentifier=revision_id,
            transactions=transactions,
        )

        from pprint import pprint
        pprint(out)

        return out

    def comment_inline(self, revision_id, issue):
        '''
        Post an inline comment on a diff
        '''
        assert isinstance(issue, ClangIssue)
        # TODO: check issue is instance of Issue
        out = self.request(
            'differential.createinline',
            revisionID=revision_id,
            filePath=issue.path,
            lineNumber=issue.line,
            lineLength=issue.nb_lines,
            isNewFile=False,  # ?
            content=issue.as_text(),
        )

        from pprint import pprint
        pprint(out)

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
        response = self.session.post(
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
