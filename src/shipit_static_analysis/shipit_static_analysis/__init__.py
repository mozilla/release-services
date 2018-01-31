# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import
from shipit_static_analysis.config import settings
from shipit_static_analysis.stats import Datadog
import os

CLANG_TIDY = 'clang-tidy'
CLANG_FORMAT = 'clang-format'
MOZLINT = 'mozlint'


class Issue(object):
    '''
    Common reported issue interface

    Several properties are also needed:
    - repo_dir: Mercurial repository directory
    - path: Source file path relative to repo_dir
    - line: Line where the issue begins
    - nb_lines: Number of lines affected by the issue
    '''
    def is_publishable(self):
        '''
        Is this issue publishable on reporters ?
        Should return a boolean
        '''
        raise NotImplementedError

    def as_text(self):
        '''
        Build the text content for reporters
        '''
        raise NotImplementedError

    def as_markdown(self):
        '''
        Build the Markdown content for debug email
        '''
        raise NotImplementedError

    def is_third_party(self):
        '''
        Is this issue in a third party path ?
        '''
        # List third party directories using mozilla-central file
        full_path = os.path.join(self.repo_dir, settings.third_party)
        assert os.path.exists(full_path), \
            'Missing third party file {}'.format(full_path)
        with open(full_path) as f:
            # Remove new lines
            third_parties = list(map(lambda l: l.rstrip(), f.readlines()))

        for path in third_parties:
            if self.path.startswith(path):
                return True
        return False


# Create common stats instance
stats = Datadog()
