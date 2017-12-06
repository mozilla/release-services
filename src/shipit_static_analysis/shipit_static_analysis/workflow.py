# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import tempfile
import hglib
import os

from cli_common.log import get_logger
from cli_common.command import run_check
from shipit_static_analysis.clang.tidy import ClangTidy
from shipit_static_analysis.clang.format import ClangFormat
from shipit_static_analysis.config import settings
from parsepatch.patch import Patch

logger = get_logger(__name__)

REPO_CENTRAL = b'https://hg.mozilla.org/mozilla-central'
REPO_REVIEW = b'https://reviewboard-hg.mozilla.org/gecko'
ARTIFACT_URL = 'https://queue.taskcluster.net/v1/task/{task_id}/runs/{run_id}/artifacts/public/results/{diff_name}'


class Workflow(object):
    '''
    Static analysis workflow
    '''
    def __init__(self, cache_root, reporters, clang_format_enabled=False):
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

        # Load reporters to use
        self.reporters = reporters
        if not self.reporters:
            logger.warn('No reporters configured, this analysis will not be published')

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

    def run(self, revision):
        '''
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
         * Publish results
        '''
        assert revision.mercurial is not None, \
            'Cannot run without a mercurial revision'

        # Add log to find Taskcluster task in papertrail
        logger.info(
            'New static analysis',
            taskcluster_task=self.taskcluster_task_id,
            taskcluster_run=self.taskcluster_run_id,
            channel=settings.app_channel,
            revision=revision,
        )

        # Setup clang
        clang_tidy = ClangTidy(self.repo_dir, settings.target)
        clang_format = ClangFormat(self.repo_dir)

        # Force cleanup to reset tip
        # otherwise previous pull are there
        self.hg.update(rev=b'tip', clean=True)

        # Pull revision from review
        self.hg.pull(source=REPO_REVIEW, rev=revision.mercurial, update=True, force=True)

        # Update to the target revision
        self.hg.update(rev=revision.mercurial, clean=True)

        # Get the parents revisions
        parent_rev = 'parents({})'.format(revision.mercurial)
        parents = self.hg.identify(id=True, rev=parent_rev).decode('utf-8').strip()

        # Find modified files by this revision
        modified_files = []
        for parent in parents.split('\n'):
            changeset = '{}:{}'.format(parent, revision.mercurial)
            status = self.hg.status(change=[changeset, ])
            modified_files += [f.decode('utf-8') for _, f in status]
        logger.info('Modified files', files=modified_files)

        # List all modified lines from current revision changes
        patch = Patch.parse_patch(
            self.hg.diff(change=revision.mercurial, git=True).decode('utf-8')
        )
        modified_lines = {
            # Use all changes in new files
            filename: diff['touched'] + diff['added']
            for filename, diff in patch.items()
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
                diff_path = os.path.join(self.taskcluster_results_dir, revision.build_diff_name())
                with open(diff_path, 'w') as f:
                    length = f.write(diff.decode('utf-8'))
                    logger.info('Diff from clang-format dumped', path=diff_path, length=length)  # noqa

                # Build diff download url
                diff_url = ARTIFACT_URL.format(
                    task_id=self.taskcluster_task_id,
                    run_id=self.taskcluster_run_id,
                    diff_name=revision.build_diff_name(),
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

        # Publish reports about these issues
        for reporter in self.reporters.values():
            reporter.publish(issues, revision, diff_url)
