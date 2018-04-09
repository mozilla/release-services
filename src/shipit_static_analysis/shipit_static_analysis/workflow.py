# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tempfile
import subprocess
import itertools
import hglib

from cli_common.command import run_check
from cli_common.log import get_logger
from shipit_static_analysis import CLANG_FORMAT
from shipit_static_analysis import CLANG_TIDY
from shipit_static_analysis import MOZLINT
from shipit_static_analysis import stats
from shipit_static_analysis.clang.format import ClangFormat
from shipit_static_analysis.clang.tidy import ClangTidy
from shipit_static_analysis.config import ARTIFACT_URL
from shipit_static_analysis.config import REPO_CENTRAL
from shipit_static_analysis.config import settings
from shipit_static_analysis.lint import MozLint

logger = get_logger(__name__)


class Workflow(object):
    '''
    Static analysis workflow
    '''
    def __init__(self, cache_root, reporters, analyzers):
        assert isinstance(analyzers, list)
        assert len(analyzers) > 0, \
            'No analyzers specified, will not run.'
        self.analyzers = analyzers
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

        # Finally, clone the mercurial repository
        self.hg = self.clone()

    @stats.api.timed('runtime.clone')
    def clone(self):
        '''
        Clone mozilla-central
        '''
        self.repo_dir = os.path.join(self.cache_root, 'sa-central')
        shared_dir = os.path.join(self.cache_root, 'sa-central-shared')
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
        return hglib.open(self.repo_dir)

    def run(self, revision):
        '''
        Run the static analysis workflow:
         * Pull revision from review
         * Checkout revision
         * Run static analysis
         * Publish results
        '''
        analyzers = []

        # Add log to find Taskcluster task in papertrail
        logger.info(
            'New static analysis',
            taskcluster_task=self.taskcluster_task_id,
            taskcluster_run=self.taskcluster_run_id,
            channel=settings.app_channel,
            revision=str(revision),
        )
        stats.api.event(
            title='Static analysis on {} for {}'.format(settings.app_channel, revision),
            text='Task {} #{}'.format(self.taskcluster_task_id, self.taskcluster_run_id),
        )
        stats.api.increment('analysis')

        with stats.api.timer('runtime.mercurial'):
            # Force cleanup to reset tip
            # otherwise previous pull are there
            self.hg.update(rev=b'tip', clean=True)
            logger.info('Set repo back to tip', rev=self.hg.tip().node)

            # Apply and analyze revision patch
            revision.apply(self.hg)
            revision.analyze_patch()

        with stats.api.timer('runtime.mach'):
            # Only run mach if revision has any C/C++ files
            if revision.has_clang_files:
                # mach configure with mozconfig
                logger.info('Mach configure...')
                run_check(['gecko-env', './mach', 'configure'], cwd=self.repo_dir)

                # Setup static analysis binaries through mach
                logger.info('Mach setup static-analysis')
                cmd = ['gecko-env', './mach', 'static-analysis', 'install']
                run_check(cmd, cwd=self.repo_dir)

                # Use clang-tidy & clang-format
                if CLANG_TIDY in self.analyzers:
                    analyzers.append(ClangTidy)
                else:
                    logger.info('Skip clang-tidy')
                if CLANG_FORMAT in self.analyzers:
                    analyzers.append(ClangFormat)
                else:
                    logger.info('Skip clang-format')

            else:
                logger.info('No clang files detected, skipping mach and clang-*')

            # Setup python environment
            logger.info('Mach lint setup...')
            cmd = ['gecko-env', './mach', 'lint', '--list']
            run_check(cmd, cwd=self.repo_dir)

            # Always use mozlint
            if MOZLINT in self.analyzers:
                analyzers.append(MozLint)
            else:
                logger.info('Skip mozlint')

        if not analyzers:
            logger.error('No analyzers to use on revision')
            return

        issues = []
        for analyzer_class in analyzers:
            # Build analyzer
            logger.info('Run {}'.format(analyzer_class.__name__))
            analyzer = analyzer_class(self.repo_dir)

            # Run analyzer on version and store generated issues
            issues += analyzer.run(revision)

        logger.info('Detected {} issue(s)'.format(len(issues)))
        if not issues:
            logger.info('No issues, stopping there.')
            return

        # Build a potential improvement patch
        self.build_improvement_patch(revision, issues)

        # Publish reports about these issues
        with stats.api.timer('runtime.reports'):
            for reporter in self.reporters.values():
                reporter.publish(issues, revision)

    def build_improvement_patch(self, revision, issues):
        '''
        Build a Diff to improve this revision (styling from clang-format)
        '''
        assert isinstance(issues, list)

        # Only use publishable issues
        # and sort them by filename
        issues = sorted(
            filter(lambda i: i.is_publishable(), issues),
            key=lambda i: i.path,
        )

        # Apply a patch on each modified file
        for filename, file_issues in itertools.groupby(issues, lambda i: i.path):
            full_path = os.path.join(self.repo_dir, filename)
            assert os.path.exists(full_path), \
                'Modified file not found {}'.format(full_path)

            # Build raw "ed" patch
            patch = '\n'.join(issue.as_diff() for issue in file_issues)
            if not patch:
                continue

            # Write patch in tmp
            _, patch_path = tempfile.mkstemp(suffix='.diff')
            with open(patch_path, 'w') as f:
                f.write(patch)

            # Apply patch on repository file
            cmd = [
                'patch',
                '-i', patch_path,
                full_path,
            ]
            exit = subprocess.run(cmd)
            assert exit.returncode == 0

            # Cleanup
            os.unlink(patch_path)

        # Get clean Mercurial diff on modified files
        files = list(map(lambda x: os.path.join(self.repo_dir, x).encode('utf-8'), revision.files))
        diff = self.hg.diff(files)
        if diff is None or diff == b'':
            logger.info('No improvement patch')
            return

        # Write diff in results directory
        diff_name = revision.build_diff_name()
        revision.diff_path = os.path.join(self.taskcluster_results_dir, diff_name)
        with open(revision.diff_path, 'w') as f:
            length = f.write(diff.decode('utf-8'))
            logger.info('Improvement diff dumped', path=revision.diff_path, length=length)  # noqa

        # Build diff download url
        revision.diff_url = ARTIFACT_URL.format(
            task_id=self.taskcluster_task_id,
            run_id=self.taskcluster_run_id,
            diff_name=diff_name,
        )
        logger.info('Diff available online', url=revision.diff_url)
