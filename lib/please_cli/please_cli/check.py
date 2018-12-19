# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import click
import click_spinner

import cli_common.cli
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
    short_help='Run tests, linters, etc.. for an PROJECT.',
    epilog='Happy hacking!',
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
def cmd(ctx,
        project,
        nix_build,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        ):
    with click_spinner.spinner():
        click.echo(f' => Testing project {project} ...', nl=False)
        outputs = ctx.invoke(please_cli.build.cmd,
                             project=project,
                             nix_path_attributes=[project],
                             interactive=False,
                             nix_build=nix_build,
                             taskcluster_secret=taskcluster_secret,
                             taskcluster_client_id=taskcluster_client_id,
                             taskcluster_access_token=taskcluster_access_token,
                             )
        if len(outputs) == 1:
            click.secho('DONE', fg='green')
        else:
            click.secho('ERROR', fg='red')


if __name__ == '__main__':
    cmd()
