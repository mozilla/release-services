# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import fnmatch
import os
import re
import subprocess

from cli_common.log import get_logger
from shipit_static_analysis import Issue
from shipit_static_analysis import stats
from shipit_static_analysis.config import CONFIG_URL
from shipit_static_analysis.config import settings
from shipit_static_analysis.revisions import Revision

logger = get_logger(__name__)

REGEX_HEADER = re.compile(r'^\s?\d{1,2}:\d{2}.\d{2} (.+):(\d+):(\d+): (warning|error|note): ([^\[\]\n]+)(?: \[([\.\w-]+)\])?$', re.MULTILINE)

ISSUE_MARKDOWN = '''
## clang-tidy {type}

- **Message**: {message}
- **Location**: {location}
- **In patch**: {in_patch}
- **Clang check**: {check}
- **Publishable check**: {publishable_check}
- **Third Party**: {third_party}
- **Expanded Macro**: {expanded_macro}
- **Publishable on MozReview**: {publishable}

```
{body}
```

{notes}
'''

ISSUE_NOTE_MARKDOWN = '''
- **Note**: {message}
- **Location**: {location}

```
{body}
```
'''

CLANG_MACRO_DETECTION = re.compile(r'^expanded from macro')

CLANG_SETUP_CMD = [
    'gecko-env',
    './mach', 'artifact', 'toolchain',
    '--from-build', 'linux64-clang-tidy'
]


class ClangTidy(object):
    '''
    Clang Tidy Parallel runner
    Inspired by run-clang-tidy.py
    '''
    def __init__(self, validate_checks=True):
        self.binary = os.path.join(
            os.environ['MOZBUILD_STATE_PATH'],
            'clang-tools', 'clang', 'bin', 'clang-tidy',
        )
        assert os.path.exists(self.binary), \
            'Missing clang-tidy in {}'.format(self.binary)

        # Verify that all specified clang-tidy checks still exist
        if validate_checks:
            for missing in self.list_missing_checks():
                logger.error('Specified clang-tidy check "{}" not found.'.format(missing))

    @stats.api.timed('runtime.clang-tidy')
    def run(self, revision):
        '''
        Run modified files with specified checks through clang-tidy
        using threaded workers (communicate through queues)
        Output a list of ClangTidyIssue
        '''
        assert isinstance(revision, Revision)
        self.revision = revision

        # Run all files in a single command
        # through mach static-analysis
        cmd = [
            'gecko-env',
            './mach', 'static-analysis', 'check',

            # Limit warnings to current files
            '--header-filter={}'.format('|'.join(
                os.path.basename(filename)
                for filename in revision.files
            )),

            '--checks={}'.format(','.join(c['name'] for c in settings.clang_checkers)),
        ] + list(revision.files)
        logger.info('Running static-analysis', cmd=' '.join(cmd))

        # Run command
        try:
            clang_output = subprocess.check_output(cmd, cwd=settings.repo_dir)
        except subprocess.CalledProcessError as e:
            logger.error('Mach static analysis failed: {}'.format(e.output))
            raise

        issues = self.parse_issues(clang_output.decode('utf-8'))

        # Report stats for these issues
        stats.report_issues('clang-tidy', issues)

        return issues

    def parse_issues(self, clang_output):
        '''
        Parse clang-tidy output into structured issues
        '''

        # Limit clang output parsing to 'Enabled checks:'
        end = re.search(r'^Enabled checks:\n', clang_output, re.MULTILINE)
        if end is not None:
            clang_output = clang_output[:end.start()-1]

        # Sort headers by positions
        headers = sorted(
            REGEX_HEADER.finditer(clang_output),
            key=lambda h: h.start()
        )

        issues = []
        for i, header in enumerate(headers):
            issue = ClangTidyIssue(header.groups())

            # Get next header
            if i+1 < len(headers):
                next_header = headers[i+1]
                issue.body = clang_output[header.end():next_header.start() - 1]
            else:
                issue.body = clang_output[header.end():]

            # Detect if issue is in patch
            issue.in_patch = issue.line in self.revision.lines.get(issue.path, [])  # noqa

            if issue.is_problem():
                # Save problem to append notes
                # Skip diagnostic errors
                if issue.check == 'clang-diagnostic-error':
                    logger.info('Skipping clang-diagnostic-error: {}'.format(issue))
                else:
                    issues.append(issue)
                    mode = issue.is_third_party() and '3rd party' or 'in-tree'
                    logger.info('Found {} code issue {}'.format(mode, issue))

            elif issues:
                # Link notes to last problem
                issues[-1].notes.append(issue)

        return issues

    def list_available_checks(self):
        '''
        Build the set of all available checks that the local clang-tidy offers
        '''
        cmd = [
            self.binary,
            '-list-checks',
            '-checks=*'
        ]
        clang_output = subprocess.check_output(cmd).decode('utf-8')
        available_checks = set(line.strip() for line in clang_output.split('\n')[1:])
        return available_checks

    def list_missing_checks(self):
        '''
        List all the clang-tidy missing checks according to config
        '''
        available_checks = self.list_available_checks()
        if len(settings.clang_checkers) > 0:
            logger.info('Available clang-tidy checks:\n\t{}'.format('\n\t'.join(available_checks)))
        else:
            logger.error('Firefox clang-tidy configuration {} should specify > 0 clang_checkers'.format(CONFIG_URL))

        return [
            check['name']
            for check in settings.clang_checkers
            if not len(fnmatch.filter(available_checks, check['name'])) > 0
        ]


class ClangTidyIssue(Issue):
    '''
    An issue reported by clang-tidy
    '''
    def __init__(self, header_data):
        assert isinstance(header_data, tuple)
        assert len(header_data) == 6
        assert not settings.repo_dir.endswith('/')
        self.path, self.line, self.char, self.type, self.message, self.check = header_data  # noqa
        if self.path.startswith(settings.repo_dir):
            self.path = self.path[len(settings.repo_dir)+1:]  # skip heading /
        self.line = int(self.line)
        self.nb_lines = 1  # Only 1 line affected on clang-tidy
        self.char = int(self.char)
        self.body = None
        self.in_patch = False
        self.notes = []

    def __str__(self):
        return '[{}] {} {} {}:{}'.format(self.type, self.check, self.path, self.line, self.char)

    def is_problem(self):
        return self.type in ('warning', 'error')

    def is_publishable(self):
        '''
        Is this issue publishable on Mozreview ?
        * not a third party code
        * check is marked as publishable
        * is in modified lines (in patch)
        * is not from an expanded macro
        '''
        return self.has_publishable_check() \
            and not self.is_third_party() \
            and not self.is_expanded_macro() \
            and self.in_patch

    def is_expanded_macro(self):
        '''
        Is the issue only found in an expanded macro ?
        '''
        if not self.notes:
            return False

        # Only consider first note
        note = self.notes[0]
        return CLANG_MACRO_DETECTION.match(note.message) is not None

    def has_publishable_check(self):
        '''
        Is this issue using a publishable check ?
        '''
        return settings.is_publishable_check(self.check)

    def as_text(self):
        '''
        Build the text body published on reporters
        '''
        body = '{}: {} [clang-tidy: {}]'.format(
            self.type.capitalize(),
            self.message.capitalize(),
            self.check,
        )

        # Add body when it's more than 2 lines
        # it generally contains useful info
        lines = len(list(filter(None, self.body.split('\n'))))
        if lines > 2:
            body += '\n{}'.format(self.body)

        return body

    def as_markdown(self):
        return ISSUE_MARKDOWN.format(
            type=self.type,
            message=self.message,
            location='{}:{}:{}'.format(self.path, self.line, self.char),
            body=self.body,
            check=self.check,
            in_patch=self.in_patch and 'yes' or 'no',
            third_party=self.is_third_party() and 'yes' or 'no',
            publishable_check=self.has_publishable_check() and 'yes' or 'no',
            publishable=self.is_publishable() and 'yes' or 'no',
            expanded_macro=self.is_expanded_macro() and 'yes' or 'no',
            notes='\n'.join([
                ISSUE_NOTE_MARKDOWN.format(
                    message=n.message,
                    location='{}:{}:{}'.format(n.path, n.line, n.char),
                    body=n.body,
                ) for n in self.notes
            ]),
        )

    def as_diff(self):
        '''
        No diff available
        '''
