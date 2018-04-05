# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import subprocess

import click
import click_spinner
import requests

import cli_common.command
import cli_common.log

import please_cli.config
import please_cli.utils


log = cli_common.log.get_logger(__name__)


class Derive:
    def __init__(self, *drv):
        self._drv = drv

    @property
    def nix_hash(self):
        return self._drv[0][0][1][11:43]


@click.command()
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--cache-url',
    'cache_urls',
    multiple=True,
    default=please_cli.config.CACHE_URLS,
    help='Locations of build artifacts.',
    )
@click.option(
    '--nix-instantiate',
    required=True,
    default='nix-instantiate',
    help='`nix-instantiate` command',
    )
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    envvar="GITHUB_BRANCH",
    required=True,
    )
def cmd(project, cache_urls, nix_instantiate, channel, indent=0, interactive=True):
    """Command to check if project is already in cache.
    """

    indent = ' ' * indent
    channel_derivations = dict()

    for tmp_channel in ['master'] + please_cli.config.DEPLOY_CHANNELS:
        project_exists = False
        attribute = project
        if tmp_channel != 'master':
            attribute += '.deploy.' + tmp_channel

        click.echo('{} => Calculating `{}` hash ... '.format(indent, attribute), nl=False)
        command = [
            nix_instantiate,
            os.path.join(please_cli.config.ROOT_DIR, 'nix/default.nix'),
            '-A', attribute
        ]
        if interactive:
            with click_spinner.spinner():
                result, output, error = cli_common.command.run(
                    command,
                    stream=True,
                    stderr=subprocess.STDOUT,
                )
        else:
            result, output, error = cli_common.command.run(
                command,
                stream=True,
                stderr=subprocess.STDOUT,
            )

        try:
            drv = output.split('\n')[-1].strip()
            with open(drv) as f:
                channel_derivations[tmp_channel] = eval(f.read())
        except Exception as e:
            log.exception(e)
            raise click.ClickException('Something went wrong when reading derivation file for `{}` project.'.format(attribute))
        click.echo('{} found.'.format(channel_derivations[tmp_channel].nix_hash))

        click.echo('{} => Checking cache if build artifacts exists for `{}` ... '.format(indent, attribute), nl=False)
        with click_spinner.spinner():
            project_exists = False
            for cache_url in cache_urls:
                response = requests.get(
                    '%s/%s.narinfo' % (cache_url, channel_derivations[tmp_channel].nix_hash),
                )
                project_exists = response.status_code == 200
                if project_exists:
                    break

        result = 1
        if project_exists:
            result = 0
        please_cli.utils.check_result(
            result,
            success_message='EXISTS',
            error_message='NOT EXISTS',
            raise_exception=False,
            ask_for_details=False,
        )

    return project_exists, channel_derivations[channel].nix_hash


if __name__ == "__main__":
    cmd()
