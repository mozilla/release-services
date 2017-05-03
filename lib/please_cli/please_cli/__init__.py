# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import sys
import click
import cli_common.log

excepthook = sys.excepthook
sys.excepthook = lambda et, e, t: click.echo("ERROR: " + str(e))  # noqa

import please_cli.utils
import please_cli.check_cache
import please_cli.github


@click.group("please")
@click.option('-D', '--debug', is_flag=True, help="TODO: add description")
@click.option('--mozdef', type=str, default=None, help="TODO: add description")
@click.pass_context
def cmd(ctx, debug, mozdef):
    """TODO: add description
    """

    cli_common.log.init_logger(debug, mozdef)

    if debug is True:
        sys.excepthook = excepthook

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cmd.add_command(please_cli.check_cache.cmd, "check-cache")
cmd.add_command(please_cli.github.cmd, "configure-taskcluster")


if __name__ == "__main__":
    cmd()
