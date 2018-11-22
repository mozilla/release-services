# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import click

from bugbug_data import config
from bugbug_data.retriever import Retriever
from bugbug_data.secrets import secrets
from cli_common.cli import taskcluster_options
from cli_common.log import init_logger


@click.command()
@taskcluster_options
@click.option(
    '--cache-root',
    required=True,
    help='Cache for repository clones.',
)
def main(cache_root,
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

    Retriever(cache_root, taskcluster_client_id, taskcluster_access_token).go()


if __name__ == '__main__':
    main()
