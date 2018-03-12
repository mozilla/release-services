# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from shipit_static_analysis.config import settings, REPO_REVIEW
from shipit_static_analysis import stats
from parsepatch.patch import Patch
from cli_common import log
import io
import hglib
import os
import re

logger = log.get_logger(__name__)


class Revision(object):
    '''
    A common DCM revision
    '''
    files = []
    lines = {}
    repo = None

    def apply(self, repo_dir):
        '''
        Apply revision to Mercurial local repository
        '''
        self.repo = hglib.open(repo_dir)

        # Load raw patch
        raw_patch = self.load_raw_patch()
        assert isinstance(raw_patch, str)
        assert raw_patch is not None and raw_patch != '', \
            'Empty raw patch'

        # List all modified lines from current revision changes
        patch = Patch.parse_patch(raw_patch, skip_comments=False)
        self.lines = {
            # Use all changes in new files
            filename: diff.get('touched', []) + diff.get('added', [])
            for filename, diff in patch.items()
        }

        # Shortcut to files modified
        self.files = self.lines.keys()

        # Apply the patch on top of repository
        self.repo.import_(
            patches=io.BytesIO(raw_patch.encode('utf-8')),
            nocommit=True,
        )

        # Report nb of files and lines analyzed
        stats.api.increment('analysis.files', len(self.files))
        stats.api.increment('analysis.lines', sum(len(line) for line in self.lines.values()))

    @property
    def has_clang_files(self):
        '''
        Check if this revision has any file that might
        be a C/C++ file
        '''
        def _is_clang(filename):
            _, ext = os.path.splitext(filename)
            return ext.lower() in settings.cpp_extensions

        return any(_is_clang(f) for f in self.files)


class PhabricatorRevision(Revision):
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
        self.id = int(groups[0])
        self.diff_phid = groups[1]

        # Load diff details to get the diff revision
        diff = self.api.load_diff(self.diff_phid)
        self.diff_id = diff['id']
        assert 'fields' in diff
        self.phid = diff['fields']['revisionPHID']
        assert self.phid.startswith('PHID-DREV')

    def __str__(self):
        return 'Phabricator #{} - {}'.format(self.diff_id, self.diff_phid)

    def build_diff_name(self):
        return '{}-clang-format.diff'.format(
            self.diff_phid,
        )

    @property
    def url(self):
        return 'https://{}/{}/'.format(self.api.hostname, self.diff_phid)

    def load_raw_patch(self):
        '''
        Load patch using Phabricator API
        '''
        return self.api.load_raw_diff(self.diff_id)


class MozReviewRevision(Revision):
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

    def load_raw_patch(self):
        '''
        Load patch using Mercurial diff
        '''
        assert self.repo is not None, \
            'No local mercurial repository instance'

        # Pull revision from review
        self.repo.pull(
            source=REPO_REVIEW,
            rev=self.mercurial,
            update=True,
            force=True,
        )

        # Build patch
        patch = self.repo.diff(change=self.mercurial, git=True)
        return patch.decode('utf-8')
