# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import click_spinner

import please_cli.config
import please_cli.utils
import please_cli.shell


CMD_HELP = '''
Run tests, linters, etc.. for an APPLICATION.

\b
APPLICATIONS:
{apps}

'''.format(
    apps=''.join([' - ' + i + '\n' for i in please_cli.config.APPS]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Run tests, linters, etc.. for an APPLICATION.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'app',
    required=True,
    type=click.Choice(please_cli.config.APPS),
    )
@click.option(
    '--nix-shell',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-shell',
    help='Path to nix-shell command (default: {}).'.format(
        please_cli.config.NIX_BIN_DIR + 'nix-shell',
        ),
    )
@click.pass_context
def cmd(ctx, app, nix_shell):
    checks = please_cli.config.APPS.get(app, {}).get('checks')

    if not checks:
        raise click.ClickException('No checks found for `{}` application.'.format(app))

    for check_title, check_command in checks:
        click.echo(' => {}: '.format(check_title), nl=False)
        with click_spinner.spinner():
            returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                                   app=app,
                                                   quiet=True,
                                                   command=check_command,
                                                   nix_shell=nix_shell,
                                                   )
        please_cli.utils.check_result(returncode, output, raise_exception=False)


if __name__ == "__main__":
    cmd()
