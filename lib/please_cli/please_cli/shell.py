# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import os
import subprocess

import cli_common.log
import please_cli.config


log = cli_common.log.get_logger(__name__)

CMD_HELP = '''

Enter development environment of an PROJECT.

\b
PROJECTS:
{projects}

EXAMPLES:

  1. for Flask / Connexion project:

  \b
  ~/d/m/services % ./please shell releng-treestatus
  [nix-shell] ~/d/m/s/s/releng_treestatus % flask run
  [nix-shell] ~/d/m/s/s/releng_treestatus % connexion run connexion run releng_treestatus/api.yml
  [nix-shell] ~/d/m/s/s/releng_treestatus % ipython
  Python 3.5.3 (default, Jan 17 2017, 07:57:56)
  In [1]: import releng_treestatus
  In [2]: exit
  [nix-shell] ~/d/m/s/s/releng_treestatus % exit

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
    short_help="Enter development environment of an PROJECT.",
    epilog="Happy hacking!",
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
def cmd(project, zsh, quiet, command, nix_shell):

    run = []
    if zsh or command:
        run.append('--run')
    if command:
        run.append(command + '; exit')
    elif zsh:
        run.append('zsh')

    _command = [
        nix_shell,
        os.path.join(please_cli.config.ROOT_DIR, 'nix/default.nix'),
        '-A', project,
        '-j', '1',
    ] + run

    os.environ['SERVICES_ROOT'] = please_cli.config.ROOT_DIR + '/'
    os.environ['SSL_DEV_CA'] = os.path.join(please_cli.config.TMP_DIR, 'certs')

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
        return os.system('PYTHONPATH="" ' + ' '.join(_command)) / 256, '', ''


if __name__ == "__main__":
    cmd()
