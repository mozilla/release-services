# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import tempfile
import urllib

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
    short_help='Update Nix dependencies for a PROJECT.',
    epilog='Happy hacking!',
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--branch-to-push',
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
    '--git-user-email',
    required=False,
    type=str,
    default='release-services+robot@mozilla.com',
    help='Git user email.',
    )
@click.option(
    '--git-user-name',
    required=False,
    type=str,
    default='Release Services Robot',
    help='Git user name.',
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
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@cli_common.cli.taskcluster_options
@click.pass_context
def cmd(ctx,
        project,
        branch_to_push,
        git_url,
        git_user_email,
        git_user_name,
        nix_shell,
        git,
        interactive,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        ):

    # if no branch is provided we assume we don't want to push changed anywhere
    # we just run the update
    if branch_to_push is None:
        return run_update(project, nix_shell, os.getcwd(), interactive)

    # a directory where we will cloned release-services
    with tempfile.TemporaryDirectory(prefix='release-services-') as root_dir:

        # if git_url is not provided we look to secrets for a value
        if git_url is None:
            logger.info(f'Trying to get repository url from secrets ({taskcluster_secret}).')
            secrets = cli_common.taskcluster.get_secrets(
                taskcluster_secret,
                project,
                required=[
                    'UPDATE_GIT_URL',
                ],
                taskcluster_client_id=taskcluster_client_id,
                taskcluster_access_token=taskcluster_access_token,
            )
            git_url = secrets['UPDATE_GIT_URL']

        dont_log = [urllib.parse.urlparse(git_url).password]

        logger.info('Cloning release-services')
        run_check(['git', 'clone', git_url, root_dir], secrets=dont_log)

        # Setup git
        logger.info('Configuring git')
        run_check(['git', 'config', 'http.postBuffer', '12M'], cwd=root_dir, secrets=dont_log)
        run_check(['git', 'config', 'user.email', git_user_email], cwd=root_dir, secrets=dont_log)
        run_check(['git', 'config', 'user.name', git_user_name], cwd=root_dir, secrets=dont_log)

        # run update on checkout
        run_update(project, nix_shell, root_dir, interactive)

        # check if there is something to commit
        output = run_check(['git', 'status', '--porcelain'], cwd=root_dir, secrets=dont_log)
        if output.strip() == "":
            logger.info('Nothing to commit.')
        else:

            # add, commit and push changed to an update branch
            logger.info('Add, commit and push changed to an update branch.')
            commit_message = f'{project}: Dependencies update.'
            run_check(['git', 'add', '.'], cwd=root_dir, secrets=dont_log)
            run_check(['git', 'commit', '-m', commit_message], cwd=root_dir, secrets=dont_log)
            run_check(['git', 'push', '-f', git_url, f'HEAD:{branch_to_push}'], cwd=root_dir, secrets=dont_log)


def run_update(project, nix_shell, root_dir, interactive):
    logger.info('Running dependency update.')
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
    please_cli.utils.check_result(
        returncode,
        output,
        raise_exception=True,
        ask_for_details=interactive,
    )


if __name__ == '__main__':
    cmd()
