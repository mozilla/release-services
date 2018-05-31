# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import please_cli.config

NAGIOS_TEMPLATE = ''''%s' => {
    parents        => 'fw1.private.releng.scl3.mozilla.net',
    check_command  => 'check_tcp2!443!2!4',
    ping_check_command => 'check_tcp2!443!2!4',
    contact_groups => '%s',
    hostgroups => [
        'releng-apps'
    ]
},'''


@click.command()
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    default=None,
    )
def cmd(channel):

    if channel is None:
        channels = please_cli.config.CHANNELS
    else:
        channels = [channel]


    for project_name in sorted(please_cli.config.PROJECTS):
        deployments = please_cli.config.PROJECTS_CONFIG.get(project_name, dict()).get('deploys', [])

        for deployment in deployments:
            channels = deployment.get('options', dict()).keys()

            for channel in channels:
                deployment_options = deployment['options'][channel]

                if 'url' not in deployment_options:
                    continue

                project_url = deployment_options['url']
                project_url = project_url.lstrip('https')
                project_url = project_url.lstrip('http')
                project_url = project_url.lstrip('://')

                contact_groups = 'shipitalerts'
                if channel == 'production':
                    contact_groups = 'build'

                click.echo(NAGIOS_TEMPLATE % (project_url, contact_groups))
