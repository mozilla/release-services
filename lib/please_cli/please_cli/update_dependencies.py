# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import subprocess

import click
import click_spinner

import cli_common.command
import cli_common.log
import cli_common.utils
import please_cli.config
import please_cli.utils


logger = cli_common.log.get_logger(__name__)

CMD_HELP = '''
Update Nix dependencies for a PROJECT.

\b
PROJECTS:
{projects}

'''.format(
    projects=''.join([' - ' + i + '\n' for i in please_cli.config.PROJECTS]),
)


def run_check(*arg, **kw):
    return cli_common.utils.retry(lambda: cli_common.command.run_check(*arg, **kw))


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Update Nix dependencies for a PROJECT.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--push-to-branch',
    required=False,
    type=str,
    default=None,
    help='Branch to which to push',
    )
@click.option(
    '--git-url',
    required=False,
    type=str,
    default=None,
    help='Git url of release-services repository.',
    )
@click.option(
    '--nix-shell',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-shell',
    help='Path to nix-shell command (default: {}).'.format(
        please_cli.config.NIX_BIN_DIR + 'nix-shell',
        ),
    )
@click.option(
    '--git',
    required=True,
    default='git',
    help='Path to git command (default: git).',
    )
@cli_common.cli.taskcluster_options
@click.pass_context
def cmd(ctx,
        project,
        push_to_branch,
        nix_shell,
        git,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        ):

    if push_to_branch is None:
        return run_update(project, nix_shell os.getcwd())

    root_dir = tempfile.mktemp(prefix="release-services-")

    if git_url is None:
        secrets = cli_common.taskcluster.get_secrets(
            taskcluster_secret,
            project,
            required=[
                'UPDATE_GIT_URL',
            ],
            taskcluster_client_id=taskcluster_client_id,
            taskcluster_access_token=taskcluster_access_token,
        )
        git_url = secrets['UPDATE_GITHUB_URL']

    # install and setup git
    run_check(['nix-env', '-f', '/etc/nix/nixpkgs', '-iA', 'git'])
    run_check(['git', 'config', '--global', 'http.postBuffer', '12M'])
    run_check(['git', 'config', '--global', 'user.email', 'release-services+robot@mozilla.com'])
    run_check(['git', 'config', '--global', 'user.name', 'Release Services Robot'])

    # clone release services
    run_check(['git', 'clone', git_url, root_dir)

    # run update on checkout
    run_update(project, nix_shell, root_dir)

    # add
    commit_message = f'{project}: Dependencies update.'
    run_check(['git', 'add', '.'], cwd=root_dir)
    run_check(['git', 'commit', '-m', commit_message],, cwd=root_dir)
    run_check(['git', 'push', '-f', 'origin', f'master:{push_to_branch}'], cwd=root_dir)


def run_update(project, nix_shell, root_dir):
    command = [
        nix_shell,
        please_cli.config.ROOT_DIR + '/nix/update.nix',
        '--argstr', 'pkg',
        project
    ]

    click.echo('Updating dependencies of {}: '.format(project), nl=False)
    with click_spinner.spinner():
        returncode, output, error = cli_common.command.run(
            command,
            stream=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=root_dir,
        )
    please_cli.utils.check_result(returncode, output, raise_exception=False)


if __name__ == "__main__":
    cmd()
