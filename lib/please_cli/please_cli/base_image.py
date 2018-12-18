# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import shutil
import subprocess

import click
import click_spinner

import cli_common.cli
import cli_common.command
import cli_common.log
import please_cli.config
import please_cli.utils

log = cli_common.log.get_logger(__name__)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help='Build base docker image.',
    epilog='Happy hacking!',
    )
@click.option(
    '--docker',
    required=True,
    default='docker',
    help='Path to docker command (default: docker).',
    )
@click.option(
    '--docker-repo',
    required=True,
    default=please_cli.config.DOCKER_BASE_REPO,
    help='Docker repository.',
    )
@click.option(
    '--docker-tag',
    required=True,
    default=please_cli.config.DOCKER_BASE_TAG,
    help='Tag of base image (default: {}).'.format(please_cli.config.DOCKER_BASE_TAG),
    )
@click.option(
    '--nix-cache-public-key',
    'nix_cache_public_keys',
    multiple=True,
    default=[],
    help='Public key for nix cache',
    )
@click.option(
    '--nix-cache-public-url',
    'nix_cache_public_urls',
    multiple=True,
    default=[],
    help='Public key for nix cache',
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@cli_common.cli.taskcluster_options
def build(docker,
          docker_repo,
          docker_tag,
          nix_cache_public_keys,
          nix_cache_public_urls,
          interactive,
          taskcluster_secret,
          taskcluster_client_id,
          taskcluster_access_token,
          ):

    secrets = cli_common.taskcluster.get_secrets(
        taskcluster_secret,
        None,
        required=[
            'NIX_CACHE_PUBLIC_KEYS',
            'NIX_CACHE_PUBLIC_URLS',
        ],
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
    )

    nix_cache_public_keys = nix_cache_public_keys or secrets['NIX_CACHE_PUBLIC_KEYS']
    nix_cache_public_urls = nix_cache_public_urls or secrets['NIX_CACHE_PUBLIC_URLS']

    docker = please_cli.utils.which(docker)
    docker_file = os.path.join(please_cli.config.ROOT_DIR, 'nix', 'docker', 'Dockerfile')
    nixpkgs_json_file = os.path.join(please_cli.config.ROOT_DIR, 'nix', 'nixpkgs.json')
    nix_json_file = os.path.join(please_cli.config.ROOT_DIR, 'nix', 'nix.json')

    temp_docker_file = os.path.join(please_cli.config.ROOT_DIR, 'Dockerfile')

    with open(nixpkgs_json_file) as f:
        nixpkgs_json = json.load(f)

    if 'rev' not in nixpkgs_json or \
       'owner' not in nixpkgs_json or \
       'repo' not in nixpkgs_json or \
       'sha256_tarball' not in nixpkgs_json:
        raise click.ClickException('`nix/nixpkgs.json` is not of correct format.')

    with open(nix_json_file) as f:
        nix_json = json.load(f)

    if 'version' not in nix_json or \
       'sha256' not in nix_json:
        raise click.ClickException('`nix/nix.json` is not of correct format.')

    try:
        shutil.copyfile(docker_file, temp_docker_file)

        click.echo(' => Building base docker image ... ', nl=False)
        with click_spinner.spinner():
            result, output, error = cli_common.command.run(
                [
                    docker,
                    'build',
                    '--no-cache',
                    '--pull',
                    '--force-rm',
                    '--build-arg', 'NIXPKGS_OWNER=' + nixpkgs_json['owner'],
                    '--build-arg', 'NIXPKGS_REPO=' + nixpkgs_json['repo'],
                    '--build-arg', 'NIXPKGS_REV=' + nixpkgs_json['rev'],
                    '--build-arg', 'NIXPKGS_SHA256=' + nixpkgs_json['sha256_tarball'],
                    '--build-arg', 'NIX_VERSION=' + nix_json['version'],
                    '--build-arg', 'NIX_SHA256=' + nix_json['sha256'],
                    '--build-arg', 'NIX_CACHE_PUBLIC_KEYS=' + ' '.join(nix_cache_public_keys),
                    '--build-arg', 'NIX_CACHE_PUBLIC_URLS=' + ' '.join(nix_cache_public_urls),
                    '-t', f'{docker_repo}:{docker_tag}',
                    please_cli.config.ROOT_DIR,
                ],
                stream=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        please_cli.utils.check_result(result, output, ask_for_details=interactive)

    finally:
        if os.path.exists(temp_docker_file):
            os.unlink(temp_docker_file)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help='Push base docker image.',
    epilog='Happy hacking!',
    )
@click.option(
    '--docker-registry',
    required=True,
    help='Docker registry.',
    default=please_cli.config.DOCKER_BASE_REGISTRY,
    )
@click.option(
    '--docker-repo',
    required=True,
    help='Docker repository.',
    default=please_cli.config.DOCKER_BASE_REPO,
    )
@click.option(
    '--docker-username',
    help='Docker username.',
    )
@click.option(
    '--docker-password',
    help='Docker password.',
    )
@click.option(
    '--docker-tag',
    required=True,
    help='Tag of base image.',
    default=please_cli.config.DOCKER_BASE_TAG,
    )
@cli_common.cli.taskcluster_options
def push(docker_registry,
         docker_repo,
         docker_username,
         docker_password,
         docker_tag,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    secrets = cli_common.taskcluster.get_secrets(
        taskcluster_secret,
        None,
        required=[
            'DOCKER_USERNAME',
            'DOCKER_PASSWORD',
        ],
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
        )

    docker_username = docker_username or secrets['DOCKER_USERNAME']
    docker_password = docker_password or secrets['DOCKER_PASSWORD']
    image_reference = f'docker-daemon:{docker_repo}:{docker_tag}'
    click.echo(' => Pushing the image to the registry ... ', nl=False)
    with click_spinner.spinner():
        please_cli.utils.push_docker_image(
            registry=docker_registry,
            username=docker_username,
            password=docker_password,
            image=image_reference,
            repo=docker_repo,
            tag=docker_tag,
        )
