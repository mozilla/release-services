# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import itertools
import tempfile
import hglib
import os

from cli_common.taskcluster import get_service
from cli_common.log import get_logger
from cli_common.command import run_check
from shipit_static_analysis.clang.tidy import ClangTidy, ClangTidyIssue
from shipit_static_analysis.clang.format import ClangFormat, ClangFormatIssue
from shipit_static_analysis.config import settings
from shipit_static_analysis.batchreview import BatchReview

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'
ARTIFACT_URL = 'https://queue.taskcluster.net/v1/task/{task_id}/runs/{run_id}/artifacts/public/results/{diff_name}'
MAX_COMMENTS = 30
MOZREVIEW_COMMENT_SUCCESS = '''
C/C++ static analysis didn't find any defects in this patch. Hooray!
'''
MOZREVIEW_COMMENT_FAILURE_SHORT = '''
C/C++ static analysis found {defects_tidy} in this patch{extras_comments}.

You can run this analysis locally with: `./mach static-analysis check path/to/file.cpp`
'''
MOZREVIEW_COMMENT_FAILURE = '''
C/C++ static analysis found {defects_total} in this patch{extras_comments}.
 - {defects_tidy} found by clang-tidy
 - {defects_format} found by clang-format

You can run this analysis locally with: `./mach static-analysis check path/to/file.cpp` and `./mach clang-format -p path/to/file.cpp`

If you see a problem in this automated review, please report it here: http://bit.ly/2y9N9Vx
'''
MOZREVIEW_COMMENT_DIFF_DOWNLOAD = '''

A full diff for the formatting issues found by clang-format is provided here: {url}

You can use it in your repository with `hg import`
'''
EMAIL_HEADER = '''{nb_publishable} Publishable issues on Mozreview

Review Url : {review_url}
Diff Url : {diff_url}
'''


class Workflow(object):
    '''
    Static analysis workflow
    '''
    taskcluster = None

    def __init__(self, cache_root, emails, app_channel, mozreview_api_root, mozreview_enabled=False, mozreview_publish_success=False, clang_format_enabled=False, mozreview_short_comment=True, client_id=None, access_token=None):  # noqa
        self.emails = emails
        self.app_channel = app_channel
        self.mozreview_api_root = mozreview_api_root
        self.mozreview_enabled = mozreview_enabled
        self.mozreview_publish_success = mozreview_publish_success
        self.mozreview_short_comment = mozreview_short_comment
        self.clang_format_enabled = clang_format_enabled
        self.cache_root = cache_root
        assert os.path.isdir(self.cache_root), \
            'Cache root {} is not a dir.'.format(self.cache_root)
        assert 'MOZCONFIG' in os.environ, \
            'Missing MOZCONFIG in environment'

        # Save Taskcluster ID for logging
        if 'TASK_ID' in os.environ and 'RUN_ID' in os.environ:
            self.taskcluster_task_id = os.environ['TASK_ID']
            self.taskcluster_run_id = os.environ['RUN_ID']
            self.taskcluster_results_dir = '/tmp/results'
        else:
            self.taskcluster_task_id = 'local instance'
            self.taskcluster_run_id = 0
            self.taskcluster_results_dir = tempfile.mkdtemp()
        if not os.path.isdir(self.taskcluster_results_dir):
            os.makedirs(self.taskcluster_results_dir)

        # Load TC services & secrets
        self.notify = get_service(
            'notify',
            client_id=client_id,
            access_token=access_token,
        )

        # Clone mozilla-central
        self.repo_dir = os.path.join(cache_root, 'central')
        shared_dir = os.path.join(cache_root, 'central-shared')
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
        '''
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
         * Publish results
        '''
        # Add log to find Taskcluster task in papertrail
        logger.info(
            'New static analysis',
            taskcluster_task=self.taskcluster_task_id,
            taskcluster_run=self.taskcluster_run_id,
            channel=self.app_channel,
            revision=revision,
            review_request_id=review_request_id,
            diffset_revision=diffset_revision,
        )

        # Setup clang
        clang_tidy = ClangTidy(self.repo_dir, settings.target)
        clang_format = ClangFormat(self.repo_dir)

        # Create batch review
        self.mozreview = BatchReview(
            self.mozreview_api_root,
            review_request_id,
            diffset_revision,
            max_comments=MAX_COMMENTS,
        )

        # Force cleanup to reset tip
        # otherwise previous pull are there
        self.hg.update(rev=b'tip', clean=True)

        # Pull revision from review
        self.hg.pull(source=REPO_REVIEW, rev=revision, update=True, force=True)

        # Update to the target revision
        self.hg.update(rev=revision, clean=True)

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

        # List all modified lines
        modified_lines = {
            f: self.mozreview.changed_lines_for_file(f)
            for f in modified_files
        }

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

        # Run static analysis through clang-tidy
        logger.info('Run clang-tidy...')
        issues = clang_tidy.run(settings.clang_checkers, modified_lines)

        # Run clang-format on modified files
        diff_url = None
        if self.clang_format_enabled:
            logger.info('Run clang-format...')
            format_issues, patched = clang_format.run(settings.cpp_extensions, modified_lines)
            issues += format_issues
            if patched:
                # Get current diff on these files
                logger.info('Found clang-format issues', files=patched)
                files = list(map(lambda x: os.path.join(self.repo_dir, x).encode('utf-8'), patched))
                diff = self.hg.diff(files)
                assert diff is not None and diff != b'', \
                    'Empty diff'

                # Write diff in results directory
                diff_name = '{}-{}-{}-clang-format.diff'.format(
                    revision[:8],
                    review_request_id,
                    diffset_revision,
                )
                diff_path = os.path.join(self.taskcluster_results_dir, diff_name)
                with open(diff_path, 'w') as f:
                    length = f.write(diff.decode('utf-8'))
                    logger.info('Diff from clang-format dumped', path=diff_path, length=length)  # noqa

                # Build diff download url
                diff_url = ARTIFACT_URL.format(
                    task_id=self.taskcluster_task_id,
                    run_id=self.taskcluster_run_id,
                    diff_name=diff_name,
                )
                logger.info('Diff available online', url=diff_url)
            else:
                logger.info('No clang-format issues')

        else:
            logger.info('Skip clang-format')

        logger.info('Detected {} issue(s)'.format(len(issues)))
        if not issues:
            logger.info('No issues, stopping there.')
            return

        # Publish on mozreview
        self.publish_mozreview(
            review_request_id,
            diffset_revision,
            issues,
            diff_url,
        )

        # Notify by email
        logger.info('Send email to admins')
        self.notify_admins(review_request_id, issues, diff_url)

    def publish_mozreview(self, review_request_id, diff_revision, issues, diff_url=None):  # noqa
        '''
        Publish comments on mozreview
        '''
        def pluralize(word, nb):
            assert isinstance(word, str)
            assert isinstance(nb, int)
            return '{} {}'.format(nb, nb == 1 and word or word + 's')

        # Filter issues to keep publishable checks
        # and non third party
        issues = list(filter(lambda i: i.is_publishable(), issues))
        if issues:
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
            extras = ' (only the first {} are reported here)'.format(MAX_COMMENTS)
            body = self.mozreview_short_comment and MOZREVIEW_COMMENT_FAILURE_SHORT or MOZREVIEW_COMMENT_FAILURE
            comment = body.format(
                extras_comments=nb > MAX_COMMENTS and extras or '',
                defects_total=pluralize('defect', nb),
                defects_format=pluralize('defect', stats.get(ClangFormatIssue, 0)),
                defects_tidy=pluralize('defect', stats.get(ClangTidyIssue, 0)),
            )
            if not self.mozreview_short_comment and diff_url is not None:
                comment += MOZREVIEW_COMMENT_DIFF_DOWNLOAD.format(
                    url=diff_url,
                )

            # Comment each issue
            for issue in issues:
                if isinstance(issue, ClangFormatIssue):
                    logger.info('Skip clang-format issue on mozreview', issue=issue)
                    continue

                if self.mozreview_enabled:
                    logger.info('Will publish about {}'.format(issue))
                    self.mozreview.comment(
                        issue.path,
                        issue.line,
                        issue.nb_lines,
                        issue.mozreview_body,
                    )
                else:
                    logger.info('Should publish about {}'.format(issue))

        elif self.mozreview_publish_success:
            comment = MOZREVIEW_COMMENT_SUCCESS
            logger.info('No issues to publish, send kudos.')

        else:
            logger.info('No issues to publish, skipping MozReview publication.')
            return

        if not self.mozreview_enabled:
            logger.info('Skipping MozReview publication.')
            return

        # Publish the review
        # without ship_it to avoid automatically r+
        return self.mozreview.publish(
            body_top=comment,
            ship_it=False,
        )

    def notify_admins(self, review_request_id, issues, diff_url):
        '''
        Send an email to administrators
        '''
        content = EMAIL_HEADER.format(
            review_url='https://reviewboard.mozilla.org/r/{}/'.format(review_request_id), # noqa
            diff_url=diff_url or 'no clang-format diff',
            nb_publishable=sum([i.is_publishable() for i in issues]),
        )
        content += '\n\n'.join([i.as_markdown() for i in issues])
        if len(content) > 102400:
            # Content is 102400 chars max
            content = content[:102000] + '\n\n... Content max limit reached!'
        subject = '[{}] New Static Analysis Review #{}'.format(self.app_channel, review_request_id)
        for email in self.emails:
            self.notify.email({
                'address': email,
                'subject': subject,
                'content': content,
                'template': 'fullscreen',
            })
