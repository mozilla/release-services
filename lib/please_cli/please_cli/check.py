# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import cli_common.cli
import click
import click_spinner
import please_cli.config
import please_cli.shell
import please_cli.utils

CMD_HELP = '''
Run tests, linters, etc.. for an PROJECT.

\b
PROJECTS:
{projects}

'''.format(
    projects=''.join([' - ' + i + '\n' for i in please_cli.config.PROJECTS]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Run tests, linters, etc.. for an PROJECT.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--nix-build',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-build',
    help='Path to nix-build command (default: {}).'.format(
        please_cli.config.NIX_BIN_DIR + 'nix-build',
        ),
    )
@cli_common.cli.taskcluster_options
@click.pass_context
def cmd(ctx, project, nix_build,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
    ):
    checks = please_cli.config.PROJECTS_CONFIG.get(project, {}).get('checks')

    if not checks:
        raise click.ClickException('No checks found for `{}` project.'.format(project))

    for check_title, check_command in checks:
        click.echo(' => {}: '.format(check_title), nl=False)
        with click_spinner.spinner():
            returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                                   project=project,
                                                   quiet=True,
                                                   command=check_command,
                                                   nix_shell=nix_build,
                                                   taskcluster_secret=taskcluster_secret,
                                                   taskcluster_client_id=taskcluster_client_id,
                                                   taskcluster_access_token=taskcluster_access_token,
                                                   )
        please_cli.utils.check_result(returncode, output, raise_exception=False)


if __name__ == "__main__":
    cmd()
