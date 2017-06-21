# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import hglib
import yaml
import os

from cli_common.taskcluster import get_service
from cli_common.log import get_logger
from cli_common.command import run_check
from rbtools.api.client import RBClient
from rbtools.api.errors import APIError
from shipit_static_analysis.clang import ClangTidy
from shipit_static_analysis.batchreview import BatchReview

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'


class Workflow(object):
    '''
    Static analysis workflow
    '''
    taskcluster = None

    def __init__(self, cache_root, emails, client_id=None, access_token=None):
        self.emails = emails
        self.cache_root = cache_root
        assert os.path.isdir(self.cache_root), \
            'Cache root {} is not a dir.'.format(self.cache_root)

        # Load TC services & secrets
        self.notify = get_service(
            'notify',
            client_id=client_id,
            access_token=access_token,
        )

        # Read local config
        config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
        self.config = yaml.load(open(config_path))
        assert 'clang_checkers' in self.config
        assert 'target' in self.config

        # Create new MozReview API client
        url = 'https://reviewboard.mozilla.org'
        username = 'jkeromnes+clangbot@mozilla.com'
        apikey = '(secret)'
        rbc = RBClient(url, save_cookies=False, allow_caching=False)
        login_resource = rbc.get_path(
            'extensions/mozreview.extension.MozReviewExtension/'
            'bugzilla-api-key-logins/')
        login_resource.create(username=username, api_key=apikey)
        self.api_root = rbc.get_root()

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
        self.clang = ClangTidy(self.repo_dir, self.config['target'])

    def run(self, revision, review_request_id, diffset_revision):
        '''
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
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
        issues = self.clang.run(self.config['clang_checkers'], modified_files)

        logger.info('Detected {} code issue(s)'.format(len(issues)))

        # Notify by email
        if issues:
            logger.info('Send email to admins')
            self.notify_admins(review_request_id, issues)
            logger.info('Post issues to MozReview')
            self.post_review(review_request_id, diffset_revision, issues)

    def notify_admins(self, review_request_id, issues):
        '''
        Send an email to administrators
        '''
        review_url = 'https://reviewboard.mozilla.org/r/' + review_request_id + '/'
        content = review_url + '\n\n' + '\n'.join([i.as_markdown() for i in issues])
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': 'New Static Analysis Review',
                'content': content,
                'template': 'fullscreen',
            })

    def post_review(self, review_request_id, diffset_revision, issues):
        '''
        Post review comments to MozReview in a single batch
        '''
        review = BatchReview(self.api_root, review_request_id, diffset_revision)
        # review.comment(filename, line, num_lines, comment)
        # review.publish(body_top='\n'.join(commentlines),
        #                ship_it=false)
