# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import requests
import please_cli.config
import please_cli.utils


class Derive:
    def __init__(self, *drv):
        self._drv = drv

    @property
    def nix_hash(self):
        return self._drv[0][0][1][11:43]


@click.command()
@click.option(
    '--cache-url',
    required=True,
    default=please_cli.config.CACHE_URL,
    help='Location of build artifacts.',
    )
@click.option(
    '--nix-instantiate',
    required=True,
    default='nix-instantiate',
    help='`nix-instantiate` command',
    )
@click.argument(
    'app',
    required=True,
    type=click.Choice(please_cli.config.APPS),
    )
@click.pass_context
def cmd(ctx, cache_url, nix_instantiate, app):
    """Command to check if application is already in cache.
    """

    code, output = please_cli.utils.run_command(
        '{nix_intantiate} {ROOT_DIR}/nix/default.nix -A apps.{app}'.format(
            nix_intantiate=nix_instantiate,
            ROOT_DIR=please_cli.config.ROOT_DIR,
            app=app,
            ))

    drv = output.split('\n')[-2].strip()

    with open(drv) as f:
        derivation = eval(f.read())

    response = requests.get('%s/%s.narinfo' % (cache_url, derivation.nix_hash))
    if response.status_code == 200:
        click.echo('EXISTS')
    else:
        click.echo('NOT EXISTS')


if __name__ == "__main__":
    cmd()
