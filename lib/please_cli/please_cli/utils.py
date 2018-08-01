# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import contextlib
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile

import click

import cli_common.command
import cli_common.log


log = cli_common.log.get_logger(__name__)


def check_result(returncode, output='', success_message='DONE',
                 error_message='ERROR', raise_exception=True,
                 ask_for_details=True, show_details=True,
                 ):
    if returncode == 0:
        click.secho(success_message, fg='green')
    else:
        click.secho(error_message, fg='red')

    if returncode != 0:
        if ask_for_details:
            show_details = click.confirm(
                '    Show details?',
                default=False,
                abort=False,
                prompt_suffix=' ',
                show_default=True,
                err=False,
            )
            if show_details:
                click.echo_via_pager(output)
        elif show_details and output:
                click.echo(output)

        if raise_exception:
            raise click.ClickException(
                'Something went wrong, please look at the logs.')


class ClickCustomCommand(click.Command):
    """A custom click command which doesn't indent help and epilog text.
    """

    def format_help_text(self, ctx, formatter):
        """Writes the help text to the formatter if it exists."""
        if self.help:
            formatter.write_paragraph()
            formatter.write_text(self.help)

    def format_epilog(self, ctx, formatter):
        """Writes the epilog into the formatter if it exists."""
        if self.epilog:
            formatter.write_paragraph()
            formatter.write_text(self.epilog)

    def format_options(self, ctx, formatter):
        """Writes all the options into the formatter if they exist."""
        opts = []
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append(rv)

        if opts:
            with formatter.section('OPTIONS'):
                formatter.write_dl(opts)


class ClickCustomGroup(click.Group, ClickCustomCommand):
    """A custom click group Command which doesn't indent help and epilog text.
    """

    def format_options(self, ctx, formatter):
        ClickCustomCommand.format_options(self, ctx, formatter)
        self.format_commands(ctx, formatter)

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if getattr(cmd, 'hidden', None):
                continue

            help = cmd.short_help or ''
            rows.append((subcommand, help))

        if rows:
            with formatter.section('COMMANDS'):
                formatter.write_dl(rows)


def which(program):
    """Find executable
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def generate_docker_auth(registry, username, password):
    """Generate docker-specific auth JSON
    """
    # b64encode accepts bytes
    auth_pair = '{}:{}'.format(username, password).encode('utf-8')
    # JSON accepts unicode
    auth_pair_base64 = base64.b64encode(auth_pair).decode('utf-8')
    return {
        'auths': {
            'https://{}/v1'.format(registry): {
                'auth': auth_pair_base64
            }
        }
    }


@contextlib.contextmanager
def authfile(registry, username, password):
    auth = generate_docker_auth(registry, username, password)
    with tempfile.TemporaryDirectory() as tempdir:

        # This file will be automatically deleted
        auth_file = os.path.join(tempdir, 'auth.json')
        with open(auth_file, 'w') as fd:
            json.dump(auth, fd)

        yield auth_file


def push_docker_image(registry, username, password, image, repo, tag,
                      interactive=False):
    with authfile(registry, username, password) as auth_file:
        command = ['skopeo', 'copy',
                   '--authfile', auth_file,
                   'docker-archive://{}'.format(image),
                   'docker://{}/{}:{}'.format(registry, repo, tag)
                  ]
        result, output, error = cli_common.command.run(
            command,
            stream=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        check_result(
            result,
            output,
            ask_for_details=interactive,
        )


def docker_image_id(image):
    """Get docker image ID

    Docker image ID corresponds to the sha256 hash of the config file
    """
    tar = tarfile.open(image)
    manifest = json.load(tar.extractfile('manifest.json'))
    config = tar.extractfile(manifest[0]['Config'])
    image_sha256 = hashlib.sha256(config.read()).hexdigest()
    return 'sha256:{}'.format(image_sha256)

