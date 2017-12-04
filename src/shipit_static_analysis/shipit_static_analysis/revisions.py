# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
from cli_common import log

logger = log.get_logger(__name__)


class PhabricatorRevision(object):
    '''
    A phabricator revision to process
    '''
    regex = re.compile(r'^(\d+):(PHID-DIFF-(?:\w+))$')

    def __init__(self, description, api):
        self.api = api

        # Parse Diff description
        match = self.regex.match(description)
        if match is None:
            raise Exception('Invalid Phabricator description')
        groups = match.groups()
        self.diff_id = int(groups[0])
        self.diff_phid = groups[1]

        # Load diff details to get the diff revision
        # and the mercurial revision
        diff = self.api.load_diff(self.diff_phid)
        assert 'fields' in diff
        self.phid = diff['fields']['revisionPHID']
        assert self.phid.startswith('PHID-DREV')
        refs = {
            ref['type']: ref
            for ref in diff['fields']['refs']
        }
        if 'base' in refs:
            self.mercurial = refs['base']['identifier']
            logger.info('Phabricator found revision', id=self.diff_id, rev=self.mercurial)
        else:
            self.mercurial = None
            logger.warn('No phabricator revision', id=self.diff_id)

        # Load revision details to get its id
        rev = self.api.load_revision(self.phid)
        self.id = rev['id']

    def __str__(self):
        return 'Phabricator #{} - {}'.format(self.diff_id, self.diff_phid)

    def build_diff_name(self):
        return '{}-clang-format.diff'.format(
            self.diff_phid,
        )

    @property
    def url(self):
        return 'https://{}/{}/'.format(self.api.hostname, self.diff_phid)


class MozReviewRevision(object):
    '''
    A mozreview revision to process
    '''
    regex = re.compile(r'^(\w+):(\d+):(\d+)$')

    def __init__(self, description):
        match = self.regex.match(description)
        if match is None:
            raise Exception('Invalid Mozreview description')

        groups = match.groups()
        self.mercurial = groups[0]
        self.review_request_id = int(groups[1])
        self.diffset_revision = int(groups[2])

    def __str__(self):
        return 'MozReview #{} - {}'.format(self.review_request_id, self.diffset_revision)

    @property
    def url(self):
        return 'https://reviewboard.mozilla.org/r/{}/'.format(self.review_request_id) # noqa

    def build_diff_name(self):
        return '{}-{}-{}-clang-format.diff'.format(
            self.mercurial[:8],
            self.review_request_id,
            self.diffset_revision,
        )
