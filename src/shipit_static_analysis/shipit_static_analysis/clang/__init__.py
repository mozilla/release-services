# -*- coding: utf-8 -*-


class ClangIssue(object):
    '''
    Common reported issue interface

    Several properties are also needed:
    - path: Source file path relative to repository
    - line: Line where the issue begins
    - nb_lines: Number of lines affected by the issue
    - mozreview_body: Build the text body published on MozReview
    '''
    def is_publishable(self):
        '''
        Is this issue publishable on Mozreview ?
        Should return a boolean
        '''
        raise NotImplementedError

    def as_markdown(self):
        '''
        Build the Markdown content for debug email
        '''
        raise NotImplementedError
