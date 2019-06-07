# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import io
import json
import os
import shutil
import tempfile
import urllib

import awscli.clidriver
import click
import click_spinner
import requests
import taskcluster.exceptions

import cli_common.cli
import cli_common.log
import cli_common.taskcluster
import please_cli.build
import please_cli.config
import please_cli.utils

log = cli_common.log.get_logger(__name__)


@click.command()
@cli_common.cli.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--s3-bucket',
    required=True,
    type=str,
    )
@click.option(
    '--subfolder',
    required=False,
    type=str,
    default='',
    )
@click.option(
    '--nix-path-attribute',
    type=str,
    required=True,
    )
@click.option(
    '--csp',
    required=False,
    multiple=True,
    default=None,
    )
@click.option(
    '--env',
    required=False,
    multiple=True,
    default=None,
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
    '--interactive/--no-interactive',
    default=True,
    )
@click.pass_context
def cmd_S3(ctx,
           project,
           s3_bucket,
           subfolder,
           nix_path_attribute,
           csp,
           env,
           nix_build,
           nix,
           taskcluster_secret,
           taskcluster_client_id,
           taskcluster_access_token,
           interactive,
           ):
    '''
    '''

    secrets = cli_common.taskcluster.get_secrets(
        taskcluster_secret,
        project,
        required=(
            'DEPLOY_S3_ACCESS_KEY_ID',
            'DEPLOY_S3_SECRET_ACCESS_KEY',
        ),
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
    )

    AWS_ACCESS_KEY_ID = secrets['DEPLOY_S3_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = secrets['DEPLOY_S3_SECRET_ACCESS_KEY']

    # 1. build project (TODO: but only pull from cache)
    project_paths = ctx.invoke(please_cli.build.cmd,
                               project=project,
                               nix_path_attributes=[nix_path_attribute],
                               nix_build=nix_build,
                               nix=nix,
                               taskcluster_secret=taskcluster_secret,
                               taskcluster_client_id=taskcluster_client_id,
                               taskcluster_access_token=taskcluster_access_token,
                               interactive=interactive,
                               )

    for project_path in project_paths:
        project_path = os.path.realpath(project_path)

        # 2. create temporary copy of project
        click.echo(' => Copying build artifacs to temporary location ... ', nl=False)
        with click_spinner.spinner():
            if not os.path.exists(please_cli.config.TMP_DIR):
                os.makedirs(please_cli.config.TMP_DIR)
            tmp_dir = tempfile.mkdtemp(
                prefix='copy-of-result-{}-'.format(project.replace('/', '-')),
                dir=please_cli.config.TMP_DIR,
            )
            shutil.rmtree(tmp_dir)
            shutil.copytree(project_path, tmp_dir, copy_function=shutil.copy)
        please_cli.utils.check_result(
            0,
            f'Copied build artifacs to temporary location: {tmp_dir}',
            ask_for_details=interactive,
        )

        # 3. apply csp and flags to index.html files
        index_html_files = []
        if os.path.exists(os.path.join(tmp_dir, 'index.html')):
            index_html_files.append('index.html')
        for item in os.listdir(tmp_dir):
            if os.path.exists(os.path.join(tmp_dir, item, 'index.html')):
                index_html_files.append(os.path.join(item, 'index.html'))

        for index_html_file in index_html_files:
            click.echo(' => Applying CSP and environment flags to index.html ... ', nl=False)
            with click_spinner.spinner():
                index_html_file = os.path.join(tmp_dir, index_html_file)
                with io.open(index_html_file, 'r', encoding='utf-8') as f:
                    index_html = f.read()
                if csp:
                    index_html = index_html.replace(
                        'font-src \'self\';',
                        'font-src \'self\'; connect-src {};'.format(' '.join(csp)),
                    )
                if env:
                    index_html = index_html.replace(
                        '<body',
                        '<body ' + (' '.join([
                            'data-{}="{}"'.format(*[j.strip() for j in i.split(':', 1)])
                            for i in env
                        ])),
                    )

                os.chmod(index_html_file, 0o755)
                with io.open(index_html_file, 'w', encoding='utf-8') as f:
                    f.write(index_html)
            please_cli.utils.check_result(
                0,
                'Applied CSP and environment flags to index.html',
                ask_for_details=interactive,
            )

        # 4. sync to S3
        click.echo(' => Syncing to S3  ... ', nl=False)
        with click_spinner.spinner():
            os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
            os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
            aws = awscli.clidriver.create_clidriver().main
            if subfolder:
                subfolder = urllib.parse.urljoin('/', subfolder)
            result = aws([
                's3',
                'sync',
                '--quiet',
                '--delete',
                '--acl', 'public-read',
                # cache for 5min only
                '--cache-control', 'max-age=5',
                # Only connect to this site and subdomains via HTTPS for the next two years
                '--metadata', 'x-amz-meta-Strict-Transport-Security=max-age=63072000;includeSubDomains',
                tmp_dir,
                's3://' + s3_bucket + subfolder,
            ])
        please_cli.utils.check_result(
            result,
            f'Synced {project} to S3 bucket {s3_bucket}',
            ask_for_details=interactive,
        )


@click.command()
@cli_common.cli.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--heroku-app',
    required=True,
    )
@click.option(
    '--heroku-username',
    required=False,
    )
@click.option(
    '--heroku-api-token',
    required=False,
    )
@click.option(
    '--heroku-dyno-type',
    required=False,
    type=click.Choice(['web', 'worker']),
    default='web'
    )
@click.option(
    '--heroku-command',
    default=None,
    type=str,
    )
@click.option(
    '--nix-path-attribute',
    type=str,
    required=True,
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
    '--docker-registry',
    required=True,
    default='registry.heroku.com',
    help='Docker registry.',
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@click.pass_context
def cmd_HEROKU(ctx,
               project,
               heroku_app,
               heroku_username,
               heroku_api_token,
               heroku_dyno_type,
               heroku_command,
               nix_path_attribute,
               nix_build,
               nix,
               taskcluster_secret,
               taskcluster_client_id,
               taskcluster_access_token,
               docker_registry,
               interactive,
               ):

    if heroku_username is None or heroku_api_token is None:
        secrets = cli_common.taskcluster.get_secrets(
            taskcluster_secret,
            project,
            required=(
                'HEROKU_USERNAME',
                'HEROKU_PASSWORD',
            ),
            taskcluster_client_id=taskcluster_client_id,
            taskcluster_access_token=taskcluster_access_token,
        )

        heroku_username = secrets['HEROKU_USERNAME']
        heroku_api_token = secrets['HEROKU_PASSWORD']

    project_paths = ctx.invoke(please_cli.build.cmd,
                               project=project,
                               nix_path_attributes=[nix_path_attribute],
                               nix_build=nix_build,
                               nix=nix,
                               taskcluster_secret=taskcluster_secret,
                               taskcluster_client_id=taskcluster_client_id,
                               taskcluster_access_token=taskcluster_access_token,
                               interactive=interactive,
                               )

    for project_path in project_paths:
        project_path = os.path.realpath(project_path)
        repo = '{}/{}'.format(heroku_app, heroku_dyno_type)
        tag = 'latest'

        click.echo(' => Pushing {} to heroku docker registry ... '.format(project), nl=False)
        with click_spinner.spinner():
            please_cli.utils.push_docker_image(
                registry=docker_registry,
                username=heroku_username,
                password=heroku_api_token,
                image=f'docker-archive://{project_path}',
                repo=repo,
                tag=tag,
                interactive=interactive,
            )

        click.echo(' => Looking up Docker ID ... ', nl=False)
        with click_spinner.spinner():
            image_id = please_cli.utils.docker_image_id(project_path)

        click.echo(' => Releasing heroku app .. ', nl=False)
        result, output = 1, 'works'
        with click_spinner.spinner():
            update = dict(
                type=heroku_dyno_type,
                docker_image=image_id,
            )
            if heroku_command:
                update['command'] = heroku_command
            r = requests.patch(
                f'https://api.heroku.com/apps/{heroku_app}/formation',
                json=dict(updates=[update]),
                headers={
                    'Accept': 'application/vnd.heroku+json; version=3.docker-releases',
                    'Authorization': f"Bearer {secrets['HEROKU_PASSWORD']}",
                },
            )
            output = r.text
            if r.status_code == 200:
                result = 0

        please_cli.utils.check_result(
            result,
            output,
            ask_for_details=interactive,
        )


@click.command()
@cli_common.cli.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--nix-path-attribute',
    type=str,
    required=True,
    )
@click.option(
    '--hook-id',
    required=True,
    )
@click.option(
    '--hook-group-id',
    required=True,
    default='project-releng'
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
    '--docker-registry',
    required=True,
    help='Docker registry.',
    )
@click.option(
    '--docker-repo',
    required=True,
    help='Docker repository.',
    )
@click.option(
    '--docker-stable-tag',
    required=False,
    help='Optional docker image tag that we overwrite with every push. Helps tracking a project using a single tag',
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@click.pass_context
def cmd_TASKCLUSTER_HOOK(ctx,
                         project,
                         nix_path_attribute,
                         hook_id,
                         hook_group_id,
                         nix_build,
                         nix,
                         taskcluster_secret,
                         taskcluster_client_id,
                         taskcluster_access_token,
                         docker_registry,
                         docker_repo,
                         docker_stable_tag,
                         interactive,
                         ):

    secrets = cli_common.taskcluster.get_secrets(
        taskcluster_secret,
        project,
        required=(
            'DOCKER_USERNAME',
            'DOCKER_PASSWORD',
        ),
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
    )

    docker_username = secrets['DOCKER_USERNAME']
    docker_password = secrets['DOCKER_PASSWORD']

    hooks_tool = cli_common.taskcluster.get_service('hooks')

    click.echo(f' => Hook `{hook_group_id}/{hook_id}` exists? ... ', nl=False)
    with click_spinner.spinner():
        hooks = [i['hookId'] for i in hooks_tool.listHooks(hook_group_id).get('hooks', [])]

    hook_exists = False
    result = 1
    output = f'Hook {hook_id} not exists in {str(hooks)}'
    if hook_id in hooks:
        hook_exists = True
        result = 0
        output = f'Hook {hook_id} exists in {str(hooks)}'

    please_cli.utils.check_result(
        result,
        output,
        success_message='EXISTS',
        error_message='NOT EXISTS',
        ask_for_details=interactive,
        raise_exception=False,
    )

    project_paths = ctx.invoke(please_cli.build.cmd,
                               project=project,
                               nix_path_attributes=[nix_path_attribute],
                               nix_build=nix_build,
                               nix=nix,
                               taskcluster_secret=taskcluster_secret,
                               taskcluster_client_id=taskcluster_client_id,
                               taskcluster_access_token=taskcluster_access_token,
                               interactive=interactive,
                               )

    for project_path in project_paths:
        project_path = os.path.realpath(project_path)

        with open(project_path) as f:
            hook = json.load(f)

        image = hook.get('task', {}).get('payload', {}).get('image', '')
        if image.startswith('/nix/store'):

            versioned_image_tag = '-'.join(reversed(image[11:-7].split('-', 1)))
            image_tags = [versioned_image_tag]
            if docker_stable_tag:
                image_tags.append(docker_stable_tag)

            for image_tag in image_tags:
                click.echo(f' => Uploading docker image `{docker_repo}:{image_tag}` ... ', nl=False)
                with click_spinner.spinner():
                    please_cli.utils.push_docker_image(
                        registry=docker_registry,
                        username=docker_username,
                        password=docker_password,
                        image=f'docker-archive://{image}',
                        repo=docker_repo,
                        tag=image_tag,
                        interactive=interactive,
                    )

            hook['task']['payload']['image'] = f'{docker_repo}:{versioned_image_tag}'

        if hook_exists:
            click.echo(f' => Updating hook `{hook_group_id}/{hook_id}` ... ', nl=False)
            with click_spinner.spinner():
                try:
                    hooks_tool.updateHook(hook_group_id, hook_id, hook)
                    result = 0
                    output = ''
                except taskcluster.exceptions.TaskclusterRestFailure as e:
                    log.exception(e)
                    output = str(e)
                    result = 1
        else:
            click.echo(f' => Creating hook `{hook_group_id}/{hook_id}` ... ', nl=False)
            with click_spinner.spinner():
                try:
                    hooks_tool.createHook(hook_group_id, hook_id, hook)
                    result = 0
                    output = ''
                except taskcluster.exceptions.TaskclusterRestFailure as e:
                    log.exception(e)
                    output = str(e)
                    result = 1

        please_cli.utils.check_result(
            result,
            output,
            ask_for_details=interactive,
        )


@click.command()
@cli_common.cli.taskcluster_options
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '--nix-path-attribute',
    type=str,
    required=True,
    )
@click.option(
    '--channel',
    type=str,
    required=False,
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
    '--docker-registry',
    required=True,
    help='Docker registry.',
    )
@click.option(
    '--docker-repo',
    required=True,
    help='Docker repository.',
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
    '--docker-stable-tag',
    required=True,
    help='Docker image tag that we overwrite with every push. Helps tracking a project using a single tag',
    )
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@click.pass_context
def cmd_DOCKERHUB(ctx,
                  project,
                  nix_path_attribute,
                  channel,
                  nix_build,
                  nix,
                  docker_registry,
                  taskcluster_secret,
                  taskcluster_client_id,
                  taskcluster_access_token,
                  docker_username,
                  docker_password,
                  docker_repo,
                  docker_stable_tag,
                  interactive,
                  ):
    '''Push to Docker Hub.

    Creates versioned ($project-$hash) and stable ($project-$nix_path_attribute-$channel) tags.
    '''

    if not (docker_username and docker_password):
        secrets = cli_common.taskcluster.get_secrets(
            taskcluster_secret,
            project,
            required=(
                'DOCKER_USERNAME',
                'DOCKER_PASSWORD',
            ),
            taskcluster_client_id=taskcluster_client_id,
            taskcluster_access_token=taskcluster_access_token,
        )
        docker_username = secrets['DOCKER_USERNAME']
        docker_password = secrets['DOCKER_PASSWORD']

    project_paths = ctx.invoke(please_cli.build.cmd,
                               project=project,
                               nix_path_attributes=[nix_path_attribute],
                               nix_build=nix_build,
                               nix=nix,
                               taskcluster_secret=taskcluster_secret,
                               taskcluster_client_id=taskcluster_client_id,
                               taskcluster_access_token=taskcluster_access_token,
                               interactive=interactive,
                               )

    for project_path in project_paths:
        project_path = os.path.realpath(project_path)
        project_basename = os.path.basename(project_path)
        # remove the docker-image-mozilla- prefix and the extension
        tag_base = project_basename.replace('docker-image-mozilla-', '').replace('.tar.gz', '')
        # Put the hash to the end of the tag
        image_tag_versioned = '-'.join(reversed(tag_base.split('-', 1)))
        for tag in (image_tag_versioned, docker_stable_tag):
            click.echo(f' => Uploading docker image `{docker_repo}:{tag}` ... ', nl=False)
            with click_spinner.spinner():
                please_cli.utils.push_docker_image(
                    registry=docker_registry,
                    username=docker_username,
                    password=docker_password,
                    image=f'docker-archive://{project_path}',
                    repo=docker_repo,
                    tag=tag,
                    interactive=interactive,
                )
