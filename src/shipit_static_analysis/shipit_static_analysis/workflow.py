# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import hglib
import os

from cli_common.taskcluster import get_service
from cli_common.log import get_logger
from cli_common.command import run_check
from shipit_static_analysis.clang import ClangTidy
from shipit_static_analysis.config import settings
from shipit_static_analysis.batchreview import BatchReview

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'


class Workflow(object):
    '''
    Static analysis workflow
    '''
    taskcluster = None

    def __init__(self, cache_root, emails, mozreview, mozreview_enabled=False, client_id=None, access_token=None):  # noqa
        self.emails = emails
        self.mozreview = mozreview
        self.mozreview_enabled = mozreview_enabled
        self.cache_root = cache_root
        assert os.path.isdir(self.cache_root), \
            'Cache root {} is not a dir.'.format(self.cache_root)

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

        # Setup clang
        self.clang = ClangTidy(self.repo_dir, settings.target)

    def run(self, revision, review_request_id, diffset_revision):
        '''
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
         * Publish results
        '''
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

        # mach configure with mozconfig
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
        issues = self.clang.run(settings.clang_checkers, modified_files)

        logger.info('Detected {} code issue(s)'.format(len(issues)))
        if not issues:
            logger.info('No issues, stopping there.')
            return

        # Publish on mozreview
        self.publish_mozreview(review_request_id, diffset_revision, issues)

        # Notify by email
        logger.info('Send email to admins')
        self.notify_admins(review_request_id, issues)

    def publish_mozreview(self, review_request_id, diff_revision, issues):
        '''
        Publish comments on mozreview
        '''

        # Filter issues to keep publishable checks
        # and non third party
        issues = list(filter(lambda i: i.is_publishable(), issues))
        if not issues:
            logger.info('No issues to publish on MozReview')
            return

        # Create batch review
        review = BatchReview(
            self.mozreview,
            review_request_id,
            diff_revision,
        )

        # Comment each issue
        for issue in issues:
            if self.mozreview_enabled:
                logger.info('Will publish about {}'.format(issue))
                review.comment(issue.path, issue.line, 1, issue.body)
            else:
                logger.info('Should publish about {}'.format(issue))

        if not self.mozreview_enabled:
            logger.info('Skipping Mozreview publication')
            return

        # Publish the review
        # without ship_it to avoid automatically r+
        return review.publish(ship_it=False)

    def notify_admins(self, review_request_id, issues):
        '''
        Send an email to administrators
        '''
        content = '{nb_publishable} Publishable issues on Mozreview\n\nUrl : {url}\n\n'.format(  # noqa
            url='https://reviewboard.mozilla.org/r/{}/'.format(review_request_id), # noqa
            nb_publishable=sum([i.is_publishable() for i in issues]),
        )
        content += '\n'.join([i.as_markdown() for i in issues])
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': 'New Static Analysis Review',
                'content': content,
                'template': 'fullscreen',
            })
