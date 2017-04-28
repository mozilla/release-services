# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import shlex
import subprocess

import click

import cli_common.log


log = cli_common.log.get_logger(__name__)


def run(command, stream=False, handle_stream_line=None, log_command=True,
        log_output=True, **kwargs):
    """Run a command through subprocess
    """

    if type(command) is str:
        command_as_string = command
        command = shlex.split(command)
    else:
        command_as_string = ' ' .join(command)

    _kwargs = dict(
        stdin=subprocess.DEVNULL,  # no interactions
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _kwargs.update(kwargs)

    if stream:
        _kwargs['bufsize'] = 1

    if log_command:
        log.debug('Running command', command=command_as_string, kwargs=_kwargs)

    with subprocess.Popen(command, **_kwargs) as proc:
        if stream:
            output = []
            for line in proc.stdout:
                line = line.decode('utf-8', 'ignore')
                line = line.rstrip('\n')
                if log_output:
                    log.debug(line)
                output.append(line)
                if handle_stream_line:
                    handle_stream_line(line)
            output = '\n'.join(output)
            # TODO: When needed we should also add possibility to stream stdout
            #  and sterr separatly using asyncio.subprocess:
            #    https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
            #  You can still pipe stderr into stdout which is enough for now.
            error = ''
        else:
            output, error = proc.communicate()

    return proc.returncode, output, error


def run_check(command, **kwargs):
    """Run a command through subprocess and check for output
    """

    if type(command) is str:
        command_as_string = command
        command = shlex.split(command)
    else:
        command_as_string = ' ' .join(command)

    returncode, output, error = run(command, **kwargs)

    if returncode != 0:
        log.critical(
            'Command failed with code: {}'.format(returncode),
            command=command_as_string,
            output=output,
            error=error,
        )
        raise click.ClickException(
            'Command (`{}`) failed with code: {}.'.format(
                command_as_string,
                returncode,
            )
        )

    return output
