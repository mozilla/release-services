# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import


class Issue(object):
    '''
    Common reported issue interface

    Several properties are also needed:
    - path: Source file path relative to repository
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
