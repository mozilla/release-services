# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
from cli_common.click import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from shipit_pulse_listener.listener import PulseListener
from shipit_pulse_listener import config


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
                              'PULSE_LISTENER_HOOKS',
                          ),
                          existing=dict(
                              PULSE_LISTENER_HOOKS=[],
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

    pl = PulseListener(secrets['PULSE_USER'],
                       secrets['PULSE_PASSWORD'],
                       secrets['PULSE_LISTENER_HOOKS'],
                       )
    click.echo('Listening to pulse messages...')
    pl.run()


if __name__ == '__main__':
    main()
