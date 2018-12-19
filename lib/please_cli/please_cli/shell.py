# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pathlib
import subprocess

import click

import cli_common.cli
import cli_common.log
import please_cli.config
import please_cli.utils

log = cli_common.log.get_logger(__name__)

CMD_HELP = '''

Enter development environment of an PROJECT.

\b
PROJECTS:
{projects}

EXAMPLES:

  1. for Flask / Connexion project:

  \b
  ~/d/m/services % ./please shell treestatus/api
  [nix-shell] ~/d/m/s/s/treestatus/api % flask run
  [nix-shell] ~/d/m/s/s/treestatus/api % connexion run connexion run treestatus_api/api.yml
  [nix-shell] ~/d/m/s/s/treestatus/api % ipython
  Python 3.5.3 (default, Jan 17 2017, 07:57:56)
  In [1]: import treestatus_api
  In [2]: exit
  [nix-shell] ~/d/m/s/s/treestatus/api % exit

  2. for Elm project:

  \b
  ~/d/m/services % ./please shell releng-frontend
  [nix-shell] ~/d/m/s/s/releng_frontend % elm repl
  [nix-shell] ~/d/m/s/s/releng_frontend % exit

'''.format(
    projects=''.join([' - ' + i + '\n' for i in please_cli.config.PROJECTS]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help='Enter development environment of an PROJECT.',
    epilog='Happy hacking!',
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--zsh',
    is_flag=True,
    help='Run in zsh',
    )
@click.option(
    '-q', '--quiet',
    is_flag=True,
    help='Don\'t display output of a command.',
    )
@click.option(
    '-C', '--command',
    default=None,
    help='Command to run in shell and then exit;',
    )
@click.option(
    '--nix-shell',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-shell',
    help='Path to nix-shell command (default: {}).'.format(
        please_cli.config.NIX_BIN_DIR + 'nix-shell',
        ),
    )
@cli_common.cli.taskcluster_options
def cmd(project, zsh, quiet, command, nix_shell,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        ):

    project_config = please_cli.config.PROJECTS_CONFIG.get(project, {})
    # run_type = project_config.get('run')
    run_options = project_config.get('run_options', {})

    TMP_DIR = pathlib.Path(please_cli.config.TMP_DIR)
    ROOT_DIR = pathlib.Path(please_cli.config.ROOT_DIR)
    CERTS_DIR = TMP_DIR / 'certs'

    ROOT_NIX_FILE = ROOT_DIR / 'nix' / 'default.nix'
    CA_CERT_FILE = CERTS_DIR / 'ca.crt'
    SERVER_CERT_FILE = CERTS_DIR / 'server.crt'
    SERVER_KEY_FILE = CERTS_DIR / 'server.key'

    run = []
    if zsh or command:
        run.append('--run')
    if command:
        run.append(command + '; exit')
    elif zsh:
        run.append('zsh')

    _command = [
        nix_shell,
        f'{ROOT_NIX_FILE}',
        '-A', project,
        '-j', '1',
    ] + run

    envs = dict(
        SERVICES_ROOT=f'{ROOT_DIR}/',
        SSL_DEV_CA=f'{CERTS_DIR}',
        SSL_CACERT=f'{CA_CERT_FILE}',
        SSL_CERT=f'{SERVER_CERT_FILE}',
        SSL_KEY=f'{SERVER_KEY_FILE}',
        HOST=run_options.get('host', os.environ.get('HOST', '127.0.0.1')),
        PORT=str(run_options.get('port', 8000)),
        RELEASE_VERSION=please_cli.config.VERSION,
        RELEASE_CHANNEL='development',
        PYTHONPATH='',
        TASKCLUSTER_SECRET=taskcluster_secret,
    )

    if taskcluster_client_id:
        envs['TASKCLUSTER_CLIENT_ID'] = taskcluster_client_id
    if taskcluster_access_token:
        envs['TASKCLUSTER_ACCESS_TOKEN'] = taskcluster_access_token

    for require in project_config.get('requires', []):
        env_name = '{}_URL'.format(please_cli.utils.normalize_name(require).upper())
        env_value = '{}://{}:{}'.format(
            please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('schema', 'https'),
            please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('host', envs['HOST']),
            please_cli.config.PROJECTS_CONFIG[require]['run_options']['port'],
        )
        envs[env_name] = env_value

    for env_name, env_value in run_options.get('envs', {}).items():
        env_name = please_cli.utils.normalize_name(env_name).upper()
        envs[env_name] = env_value

    click.echo(' => Setting environment variables:')
    for env_name, env_value in envs.items():
        click.echo(f'    - {env_name}="{env_value}"')
        os.environ[env_name] = env_value

    if command:
        handle_stream_line = None
        if quiet is False:
            handle_stream_line = click.echo
        return cli_common.command.run(
            _command,
            stream=True,
            handle_stream_line=handle_stream_line,
            stderr=subprocess.STDOUT,
        )
    else:
        log.debug('Running command using os.system', command=_command)
        return os.system(' '.join(_command)) / 256, '', ''


@click.command()
def cmd_docker_shell():
    os.execl('/bin/bash', '/bin/bash')


if __name__ == '__main__':
    cmd()
