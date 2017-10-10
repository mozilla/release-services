# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
from shipit_bot_uplift.sync import Bot
from shipit_bot_uplift import config
from shipit_bot_uplift.api import api_client
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from cli_common.click import taskcluster_options


@click.command()
@taskcluster_options
@click.argument('bugzilla_id', type=int, required=False)
@click.option(
    '--cache-root',
    default=config.DEFAULT_CACHE,
    help='Cache for repository clones.',
)
def main(bugzilla_id,
         cache_root,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):
    '''
    Run bot to sync bug & analysis on a remote server
    '''

    # load secrets
    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          required=(
                              'BUGZILLA_URL',
                              'BUGZILLA_TOKEN',
                              'API_URL',
                              'APP_CHANNEL',
                              'UPLIFT_NOTIFICATIONS',
                          ),
                          existing=dict(
                              APP_CHANNEL='development',
                              UPLIFT_NOTIFICATIONS=['babadie@mozilla.com'],
                          ),
                          taskcluster_client_id=taskcluster_client_id,
                          taskcluster_access_token=taskcluster_access_token,
                          )

    # setup logging
    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    # Setup credentials for Shipit api
    api_client.setup(
        secrets['API_URL'],
        secrets.get('TASKCLUSTER_CLIENT_ID', taskcluster_client_id),
        secrets.get('TASKCLUSTER_ACCESS_TOKEN', taskcluster_access_token),
    )

    bot = Bot(secrets['APP_CHANNEL'], secrets['UPLIFT_NOTIFICATIONS'])
    bot.use_bugzilla(
        secrets['BUGZILLA_URL'],
        secrets['BUGZILLA_TOKEN'],
    )
    bot.use_cache(cache_root)
    if bugzilla_id:
        bot.run(only=[bugzilla_id, ])
    else:
        bot.run()


if __name__ == '__main__':
    main()
