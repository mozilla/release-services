# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import click

from cli_common.cli import taskcluster_options
from cli_common.log import init_logger
from code_coverage_bot import config
from code_coverage_bot.codecov import CodeCov
from code_coverage_bot.secrets import secrets


@click.command()
@taskcluster_options
@click.option('--repository', envvar='REPOSITORY')
@click.option('--revision', envvar='REVISION')
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
@click.option(
    '--task-name-filter',
    default='*',
    help='Filter Taskcluster tasks using a glob expression',
)
def main(repository,
         revision,
         cache_root,
         task_name_filter,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):
    secrets.load(taskcluster_secret, taskcluster_client_id, taskcluster_access_token)

    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    c = CodeCov(repository, revision, task_name_filter, cache_root, taskcluster_client_id, taskcluster_access_token)
    c.go()


if __name__ == '__main__':
    main()
