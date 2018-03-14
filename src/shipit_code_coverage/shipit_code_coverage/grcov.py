# -*- coding: utf-8 -*-
from cli_common.log import get_logger
from cli_common.command import run_check


logger = get_logger(__name__)


def report(artifacts, source_dir=None, service_number=None, commit_sha='unused', token='unused', out_format='coveralls', options=[]):
    cmd = [
      'grcov',
      '-t', out_format,
      '-p', '/home/worker/workspace/build/src/',
      '--ignore-dir', 'gcc',
    ]

    if 'coveralls' in out_format:
        cmd.extend([
          '--service-name', 'TaskCluster',
          '--commit-sha', commit_sha,
          '--token', token,
          '--service-job-number', '1',
        ])

        if service_number is not None:
            cmd.extend(['--service-number', str(service_number)])

    if source_dir is not None:
        cmd.extend(['-s', source_dir])
        cmd.append('--ignore-not-existing')

    cmd.extend(artifacts)
    cmd.extend(options)

    return run_check(cmd)


def files_list(artifacts, source_dir=None):
    options = ['--filter-covered', '--threads', '2']
    files = report(artifacts, source_dir=source_dir, out_format='files', options=options)
    return files.decode('utf-8').splitlines()
