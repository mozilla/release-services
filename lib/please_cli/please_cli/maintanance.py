# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click


@click.command()
@click.argument('projects', nargs=-1)
def cmd_on(projects):
    click.echo('TODO: maintanance ON')


@click.command()
@click.argument('projects', nargs=-1)
def cmd_off(projects):
    click.echo('TODO: maintanance OFF')
