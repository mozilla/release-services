# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
from cli_common.click import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from shipit_code_coverage.codecov import CodeCov
from shipit_code_coverage import config


@click.command()
@taskcluster_options
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
def main(cache_root,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          required=(
                              config.COVERALLS_TOKEN_FIELD,
                              config.CODECOV_TOKEN_FIELD,
                          ),
                          taskcluster_client_id=taskcluster_client_id,
                          taskcluster_access_token=taskcluster_access_token,
                          )

    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    c = CodeCov(cache_root,
                secrets[config.COVERALLS_TOKEN_FIELD],
                secrets[config.CODECOV_TOKEN_FIELD],
                )
    c.go()


if __name__ == '__main__':
    main()
