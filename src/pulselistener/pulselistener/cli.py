# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import click

from cli_common.cli import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from pulselistener import config
from pulselistener import task_monitoring
from pulselistener.listener import PulseListener


@click.command()
@taskcluster_options
def main(taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          required=(
                              'PULSE_USER',
                              'PULSE_PASSWORD',
                              'HOOKS',
                              'ADMINS',
                          ),
                          existing=dict(
                              HOOKS=[],
                              ADMINS=['babadie@mozilla.com', 'mcastelluccio@mozilla.com']
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

    task_monitoring.emails = secrets['ADMINS']

    pl = PulseListener(secrets['PULSE_USER'],
                       secrets['PULSE_PASSWORD'],
                       secrets['HOOKS'],
                       taskcluster_client_id,
                       taskcluster_access_token,
                       )
    click.echo('Listening to pulse messages...')
    pl.run()


if __name__ == '__main__':
    main()
