# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
from shipit_static_analysis.clang.tidy import ClangTidyIssue
from shipit_static_analysis.clang.format import ClangFormatIssue

COMMENT_FAILURE_SHORT = '''
C/C++ static analysis found {defects_tidy} in this patch{extras_comments}.

You can run this analysis locally with: `./mach static-analysis check path/to/file.cpp`
'''
COMMENT_FAILURE = '''
C/C++ static analysis found {defects_total} in this patch{extras_comments}.
 - {defects_tidy} found by clang-tidy
 - {defects_format} found by clang-format

You can run this analysis locally with: `./mach static-analysis check path/to/file.cpp` and `./mach clang-format -p path/to/file.cpp`
'''
BUG_REPORT = '''
If you see a problem in this automated review, please report it here: http://bit.ly/2y9N9Vx
'''
COMMENT_DIFF_DOWNLOAD = '''

A full diff for the formatting issues found by clang-format is provided here: {url}

You can use it in your repository with `hg import` or `git apply`
'''


class Reporter(object):
    '''
    Common interface to post reports on a website
    Will configure & build reports
    '''
    def __init__(self, configuration, client_id, access_token):
        '''
        Configure reporter using Taskcluster credentials and configuration
        '''
        raise NotImplementedError

    def publish(self, issues, revision, diff_url):
        '''
        Publish a new report
        '''
        raise NotImplementedError

    def requires(self, configuration, *keys):
        '''
        Check all configuration necessary keys are present
        '''
        assert isinstance(configuration, dict)

        out = []
        for key in keys:
            assert key in configuration, \
                'Missing {} {}'.format(self.__class__.__name__, key)
            out.append(configuration[key])

        return out

    def build_comment(self, issues, style='full', diff_url=None, max_comments=None):
        '''
        Build a human readable comment about published issues
        '''
        assert style in ('full', 'clang-tidy')

        def pluralize(word, nb):
            assert isinstance(word, str)
            assert isinstance(nb, int)
            return '{} {}'.format(nb, nb == 1 and word or word + 's')

        # Calc stats for issues, grouped by class
        stats = {
            cls: len(list(items))
            for cls, items in itertools.groupby(sorted([
                issue.__class__
                for issue in issues
            ], key=lambda x: str(x)))
        }

        # Build top comment
        nb = len(issues)
        extras = ''
        if max_comments is not None and nb > max_comments:
            extras = ' (only the first {} are reported here)'.format(max_comments)

        body = style == 'clang-tidy' and COMMENT_FAILURE_SHORT or COMMENT_FAILURE
        comment = body.format(
            extras_comments=extras,
            defects_total=pluralize('defect', nb),
            defects_format=pluralize('defect', stats.get(ClangFormatIssue, 0)),
            defects_tidy=pluralize('defect', stats.get(ClangTidyIssue, 0)),
        )
        comment += BUG_REPORT
        if style == 'full' and diff_url is not None:
            comment += COMMENT_DIFF_DOWNLOAD.format(
                url=diff_url,
            )
        return comment
