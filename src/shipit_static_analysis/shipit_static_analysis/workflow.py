# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import hglib
import os
import re

from cli_common.taskcluster import get_service
from cli_common.log import get_logger
from cli_common.command import run_check

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'

REGEX_HEADER = re.compile(r'^(.+):(\d+):(\d+): (warning|error|note): (.*)\n', re.MULTILINE)


class Issue(object):
    """
    An issue reported by clang-tidy
    """
    def __init__(self, header_data, work_dir):
        assert isinstance(header_data, tuple)
        assert len(header_data) == 5
        self.path, self.line, self.char, self.type, self.message = header_data
        if self.path.startswith(work_dir):
            self.path = self.path[len(work_dir):]
        self.line = int(self.line)
        self.char = int(self.char)
        self.body = None
        self.notes = []

    def __str__(self):
        return '[{}] {} {}:{}'.format(self.type, self.path, self.line, self.char)

    def is_problem(self):
        return self.type in ('warning', 'error')

    def as_markdown(self):
        out = [
            '# {} : {}'.format(self.type, self.path),
            '**Position**: {}:{}'.format(self.line, self.char),
            '**Snippet**: {}'.format(self.message),
            '',
        ]
        out += [
            '* note on {} at {}:{} : {}'.format(
                n.path, n.line, n.char, n.message
            )
            for n in self.notes
        ]
        return '\n'.join(out)


class Workflow(object):
    """
    Static analysis workflow
    """
    taskcluster = None

    def __init__(self, cache_root, emails, client_id=None, access_token=None):
        self.emails = emails
        self.cache_root = cache_root
        assert os.path.isdir(self.cache_root), \
            "Cache root {} is not a dir.".format(self.cache_root)

        # Load TC services & secrets
        self.notify = get_service(
            'notify',
            client_id=client_id,
            access_token=access_token,
        )

        # Clone mozilla-central
        self.repo_dir = os.path.join(self.cache_root, 'static-analysis/')
        shared_dir = os.path.join(self.cache_root, 'static-analysis-shared')
        logger.info('Clone mozilla central', dir=self.repo_dir)
        cmd = hglib.util.cmdbuilder('robustcheckout',
                                    REPO_CENTRAL,
                                    self.repo_dir,
                                    purge=True,
                                    sharebase=shared_dir,
                                    branch=b'tip')

        cmd.insert(0, hglib.HGPATH)
        proc = hglib.util.popen(cmd)
        out, err = proc.communicate()
        if proc.returncode:
            raise hglib.error.CommandError(cmd, proc.returncode, out, err)

        # Open new hg client
        self.hg = hglib.open(self.repo_dir)

    def run(self, revision, review_request_id, diffset_revision):
        """
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
        """
        # Force cleanup to reset tip
        # otherwise previous pull are there
        self.hg.update(rev=b'tip', clean=True)

        # Pull revision from review
        logger.info('Pull from review', revision=revision)
        self.hg.pull(source=REPO_REVIEW, rev=revision, update=True, force=True)

        # Get the parents revisions
        parent_rev = 'parents({})'.format(revision)
        parents = self.hg.identify(id=True, rev=parent_rev).decode('utf-8').strip()

        # Find modified files by this revision
        modified_files = []
        for parent in parents.split('\n'):
            changeset = '{}:{}'.format(parent, revision)
            status = self.hg.status(change=[changeset, ])
            modified_files += [f.decode('utf-8') for _, f in status]
        logger.info('Modified files', files=modified_files)

        # mach configure
        logger.info('Mach configure...')
        run_check(['gecko-env', './mach', 'configure'], cwd=self.repo_dir)

        # Build CompileDB backend
        logger.info('Mach build backend...')
        cmd = ['gecko-env', './mach', 'build-backend', '--backend=CompileDB']
        run_check(cmd, cwd=self.repo_dir)

        # Build exports
        logger.info('Mach build exports...')
        run_check(['gecko-env', './mach', 'build', 'pre-export'], cwd=self.repo_dir)
        run_check(['gecko-env', './mach', 'build', 'export'], cwd=self.repo_dir)

        # Run static analysis through run-clang-tidy.py
        logger.info('Run clang-tidy...')
        checks = [
            '-*',
            'modernize-loop-convert',
            'modernize-use-auto',
            'modernize-use-default',
            'modernize-raw-string-literal',
            'modernize-use-bool-literals',
            'modernize-use-override',
            'modernize-use-nullptr',
        ]
        cmd = [
            'run-clang-tidy.py',
            '-j', '18',
            '-p', 'obj-x86_64-pc-linux-gnu/',
            '-checks={}'.format(','.join(checks)),
        ] + modified_files
        clang_output = run_check(cmd, cwd=self.repo_dir).decode('utf-8')

        # Parse clang-tidy's output to indentify potential code problems
        logger.info('Process static analysis results...')
        issues = self.parse_issues(clang_output)

        logger.info('Detected {} code issue(s)'.format(len(issues)))

        # Notify by email
        if issues:
            logger.info('Send email to admins')
            self.notify_admins(review_request_id, issues)

    def parse_issues(self, clang_output):
        """
        Parse clang-tidy output into structured issues
        """

        # Limit clang output parsing to "Enabled checks:"
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
            issue = Issue(header.groups(), self.repo_dir)

            # Get next header
            if i+1 < len(headers):
                next_header = headers[i+1]
                issue.body = clang_output[header.end():next_header.start() - 1]
            else:
                issue.body = clang_output[header.end():]

            if issue.is_problem():
                # Save problem to append notes
                issues.append(issue)
                logger.info('Found code issue {}'.format(issue))

            elif issues:
                # Link notes to last problem
                issues[-1].notes.append(issue)

        return issues

    def notify_admins(self, review_request_id, issues):
        """
        Send an email to administrators
        """
        review_url = 'https://reviewboard.mozilla.org/r/' + review_request_id + '/'
        content = review_url + '\n\n' + '\n'.join([i.as_markdown() for i in issues])
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': 'New Static Analysis Review',
                'content': content,
                'template': 'fullscreen',
            })
