# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import subprocess
import tempfile

import click
import click_spinner

import cli_common.taskcluster
import cli_common.command
import cli_common.click
import please_cli.config
import please_cli.utils


@click.command(
    short_help="Build a project.",
)
@cli_common.click.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
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
    '--nix',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix',
    help='`nix` command',
    )
@click.option(
    '--cache-bucket',
    required=False,
    default=None,
    )
@click.option(
    '--cache-region',
    required=False,
    default=None,
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
def cmd(project,
        extra_attribute,
        nix_build,
        nix,
        cache_bucket,
        cache_region,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        interactive,
        ):

    required_secrets = [
        'NIX_CACHE_SECRET_KEYS',
    ]

    if cache_bucket and cache_region:
        required_secrets += [
            'CACHE_ACCESS_KEY_ID',
            'CACHE_SECRET_ACCESS_KEY',
        ]

    secrets = cli_common.taskcluster.get_secrets(taskcluster_secret,
                                                 project,
                                                 required=required_secrets,
                                                 )

    click.echo(' => Building {} project ... '.format(project), nl=False)
    with click_spinner.spinner():
        temp_files =  []
        nix_cache_secret_keys = []
        for secret_key in secrets['NIX_CACHE_SECRET_KEYS']:
            fd, temp_file = tempfile.mkstemp(text=True)
            with open(temp_file, 'w') as f:
                f.write(secret_key)
            os.close(fd)
            nix_cache_secret_keys += [
                '--option',
                'secret-key-files',
                temp_file,
            ]

        for attribute in [project] + list(extra_attribute):
            command = [
                nix_build,
                please_cli.config.ROOT_DIR + '/nix/default.nix',
                '-A', attribute,
                '-o', please_cli.config.TMP_DIR + '/result-build-{project}-{attribute}'.format(
                    project=project,
                    attribute=attribute.lstrip(project + '.'),
                ),
            ] + nix_cache_secret_keys
            result, output, error = cli_common.command.run(
                command,
                stream=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if result != 0:
                break

        for temp_file in temp_files:
            os.remove(temp_file)

    please_cli.utils.check_result(
        result,
        output,
        ask_for_details=interactive,
    )

    if cache_bucket and cache_region:
        tmp_cache_dir = os.path.join(please_cli.config.TMP_DIR, 'cache')
        if not os.path.exists(tmp_cache_dir):
            os.makedirs(tmp_cache_dir)

        build_results = [
            os.path.join(please_cli.config.TMP_DIR, item)
            for item in os.listdir(please_cli.config.TMP_DIR)
            if item.startswith('result-build-' + project)
        ]

        os.environ['AWS_ACCESS_KEY_ID'] = secrets['CACHE_ACCESS_KEY_ID']
        os.environ['AWS_SECRET_ACCESS_KEY'] = secrets['CACHE_SECRET_ACCESS_KEY']
        command = [
            nix, 'copy',
            '--to', 's3://{}?region={}'.format(cache_bucket, cache_region),
            '-vvvv',
        ] + build_results
        click.echo(' => Creating cache artifacts for {} project... '.format(project), nl=False)
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


@click.command(
    short_help="Build the docker image of a project.",
)
@cli_common.click.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--nix-build',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-build',
    help='`nix-build` command',
    )
@click.option(
    '--docker',
    required=True,
    default='docker',
    help='Path to docker binary on your host',
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@click.option(
    '--load-image/--no-load-image',
    help='Load the generated image into docker',
    default=True,
    )
def cmd_docker(project,
        nix_build,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        docker,
        interactive,
        load_image,
    ):

    image_path = please_cli.config.TMP_DIR + '/result-docker-{project}'.format(project=project)

    # Build docker image for project
    click.echo(' => Building docker image for {}'.format(project))
    with click_spinner.spinner():
        command = [
            nix_build,
            please_cli.config.ROOT_DIR + '/nix/default.nix',
            '-A', '{}.docker'.format(project),
            '-o', image_path
        ]
        result, output, error = cli_common.command.run(
            command,
            stream=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    please_cli.utils.check_result(
        result,
        output,
        ask_for_details=interactive,
    )

    if not load_image:
        click.echo('You can load the image with this command: \n$ {docker} load -i {image_path}'.format(
            docker=docker,
            image_path=image_path,
        ))
        return

    # Loading docker image
    click.echo(' => Importing docker image from {}'.format(image_path))
    with click_spinner.spinner():
        command = [
            docker,
            'load',
            '-i', image_path,
        ]
        result, output, error = cli_common.command.run(
            command,
            stream=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    please_cli.utils.check_result(
        result,
        output,
        ask_for_details=interactive,
    )

    click.echo(' => Image loaded')


if __name__ == "__main__":
    cmd()
