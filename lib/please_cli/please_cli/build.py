# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import subprocess

import awscli.clidriver
import click
import click_spinner

import cli_common.taskcluster
import cli_common.command
import please_cli.config
import please_cli.utils


@click.command()
@click.argument(
    'app',
    required=True,
    type=click.Choice(please_cli.config.APPS),
    )
@click.option(
    '--extra-attribute',
    multiple=True,
    )
@click.option(
    '--nix-build',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-build',
    help='`nix-build` command',
    )
@click.option(
    '--nix-push',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-push',
    help='`nix-push` command',
    )
@click.option(
    '--cache-bucket',
    required=False,
    default=None,
    )
@click.option(
    '--taskcluster-secrets',
    required=True,
    )
@click.option(
    '--taskcluster-client-id',
    default=None,
    required=False,
    )
@click.option(
    '--taskcluster-access-token',
    default=None,
    required=False,
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
def cmd(app,
        extra_attribute,
        nix_build,
        nix_push,
        cache_bucket,
        taskcluster_secrets,
        taskcluster_client_id,
        taskcluster_access_token,
        interactive,
        ):

    secrets = dict()

    if cache_bucket:
        taskcluster = cli_common.taskcluster.TaskclusterClient(
            taskcluster_client_id,
            taskcluster_access_token,
        )
        secrets_tool = taskcluster.get_service('secrets')
        secrets = secrets_tool.get(taskcluster_secrets)['secret']

        AWS_ACCESS_KEY_ID = secrets.get('CACHE_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = secrets.get('CACHE_SECRET_ACCESS_KEY')

        if AWS_ACCESS_KEY_ID is None or AWS_SECRET_ACCESS_KEY is None:
            raise click.UsageError(click.wrap_text(
                'ERROR: CACHE_ACCESS_KEY_ID and/or CACHE_SECRET_ACCESS_KEY '
                'are not in Taskcluster secret (`{}`).'.format(taskcluster_secrets)
            ))

    click.echo(' => Building {} application ... '.format(app), nl=False)
    with click_spinner.spinner():
        for index, attribute in enumerate([app] + list(extra_attribute)):
            command = [
                nix_build,
                please_cli.config.ROOT_DIR + '/nix/default.nix',
                '-A', attribute,
                '-o', please_cli.config.TMP_DIR + '/result-build-{app}-{index}'.format(app=app, index=index),
            ]
            result, output, error = cli_common.command.run(
                command,
                stream=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result != 0:
                break
    please_cli.utils.check_result(
        result,
        output,
        ask_for_details=interactive,
    )

    if cache_bucket:
        tmp_cache_dir = os.path.join(please_cli.config.TMP_DIR, 'cache')
        if not os.path.exists(tmp_cache_dir):
            os.makedirs(tmp_cache_dir)

        build_results = [
            os.path.join(please_cli.config.TMP_DIR, item)
            for item in os.listdir(please_cli.config.TMP_DIR)
            if item.startswith('result-build-' + app)
        ]

        command = [
            nix_push,
            '--dest', tmp_cache_dir,
            '--force',
        ] + build_results
        click.echo(' => Creating cache artifacts for {} application... '.format(app), nl=False)
        with click_spinner.spinner():
            result, output, error = cli_common.command.run(
                command,
                stream=True,
                stderr=subprocess.STDOUT,
            )
        please_cli.utils.check_result(
            result,
            output,
            ask_for_details=interactive,
        )

        os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
        os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
        aws = awscli.clidriver.create_clidriver().main
        click.echo(' => Pushing cache artifacts of {} to S3 ... '.format(app), nl=False)
        with click_spinner.spinner():
            result = aws([
                's3',
                'sync',
                '--quiet',
                '--size-only',
                '--acl', 'public-read',
                tmp_cache_dir,
                's3://' + cache_bucket,
            ])
        please_cli.utils.check_result(result, output)


if __name__ == "__main__":
    cmd()
