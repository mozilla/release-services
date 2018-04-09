# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tempfile

import hglib

from cli_common.command import run_check
from cli_common.log import get_logger
from shipit_static_analysis import CLANG_FORMAT
from shipit_static_analysis import CLANG_TIDY
from shipit_static_analysis import MOZLINT
from shipit_static_analysis import stats
from shipit_static_analysis.clang.format import ClangFormat
from shipit_static_analysis.clang.tidy import ClangTidy
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

        issues = []
        for analyzer_class in analyzers:
            # Build analyzer
            logger.info('Run {}'.format(analyzer_class.__name__))
            analyzer = analyzer_class(self.repo_dir)

            # Run analyzer on version and store generated issues
            issues += analyzer.run(revision)

        # Publish reports about these issues
        return
        with stats.api.timer('runtime.reports'):
            for reporter in self.reporters.values():
                reporter.publish(issues, revision)
