# -*- coding: utf-8 -*-
import os
import shutil
import tarfile

from cli.common_log import get_logger
from cli_common.command import run_check
from code_coverage_bot import grcov

logger = get_logger(__name__)


def generate(suites, artifactsHandler, ccov_reports_dir, repo_dir):
    for suite in suites:
        output = grcov.report(artifactsHandler.get(suite=suite), out_format='lcov')

        info_file = os.path.join(ccov_reports_dir, '%s.info' % suite)

        with open(info_file, 'wb') as f:
            f.write(output)

        suite_dir = os.path.join(ccov_reports_dir, suite)
        run_check([
            'genhtml',
            '-o', suite_dir,
            '--show-details', '--highlight', '--ignore-errors', 'source',
            '--legend', info_file,
            '--prefix', repo_dir
        ], cwd=repo_dir)

        os.remove(info_file)

        with tarfile.open(os.path.join(ccov_reports_dir, '%s.tar.xz' % suite), 'w:xz') as tar:
            tar.add(suite_dir, arcname=suite)
        shutil.rmtree(suite_dir)

        logger.info('Suite report generated', suite=suite)
