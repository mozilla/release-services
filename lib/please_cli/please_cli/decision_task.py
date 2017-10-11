# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import json

import click
import click_spinner
import slugid

import cli_common.taskcluster
import please_cli.config


DEPLOYABLE_PROJECTS = {}
for project_name, project_config in please_cli.config.PROJECTS.items():
    if 'deploy' in project_config:
        DEPLOYABLE_PROJECTS[project_name] = project_config


def get_build_task(index,
                   project,
                   task_group_id,
                   parent_task,
                   github_commit,
                   owner,
                   channel,
                   ):

    project_config = please_cli.config.PROJECTS.get(project, {})

    extra_attributes = []
    if channel in project_config.get('deploy_options', {}).keys():
        extra_attributes = [
            '--extra-attribute="{}.deploy.{}"'.format(project, channel),
        ]

    command = [
        './please', '-vv', 'tools', 'build', project,
        '--cache-bucket="releng-cache"',
        '--taskcluster-secret=repo:github.com/mozilla-releng/services:branch:' + channel,
        '--no-interactive',
    ] + extra_attributes
    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        channel,
        ' '.join(command),
        {
            'name': '1.{index:02}. Building {project}'.format(
                index=index + 1,
                project=project,
            ),
            'description': '',
            'owner': owner,
            'source': 'https://github.com/mozilla-releng/services/tree/' + channel,

        },
        max_run_time_in_hours=5,
    )


def get_deploy_task(index,
                    project,
                    task_group_id,
                    parent_task,
                    github_commit,
                    owner,
                    channel,
                    ):

    project_config = please_cli.config.PROJECTS.get(project, {})
    deploy_type = project_config.get('deploy')
    deploy_options = project_config.get('deploy_options', {}).get(channel, {})
    scopes = []

    extra_attributes = []
    if channel in project_config.get('deploy_options', {}).keys():
        extra_attributes = [
            '--extra-attribute="{}.deploy.{}"'.format(project, channel),
        ]

    if deploy_type == 'S3':
        project_csp = []
        for url in deploy_options.get('csp', []):
            project_csp.append('--csp="{}"'.format(url))
        for require in project_config.get('requires', []):
            require_config = please_cli.config.PROJECTS.get(require, {})
            require_deploy_options = require_config.get('deploy_options', {}).get(channel, {})
            require_url = require_deploy_options.get('url')
            if require_url:
                project_csp.append('--csp="{}"'.format(require_url))

        project_envs = []
        project_envs.append('--env="release-version: {}"'.format(please_cli.config.VERSION))
        project_envs.append('--env="release-channel: {}"'.format(channel))
        for env_name, env_value in deploy_options.get('envs', {}).items():
            project_envs.append('--env="{}: {}"'.format(env_name, env_value))
        for require in project_config.get('requires', []):
            require_config = please_cli.config.PROJECTS.get(require, {})
            require_deploy_options = require_config.get('deploy_options', {}).get(channel, {})
            require_url = require_deploy_options.get('url')
            if require_url:
                project_envs.append('--env="{}-url: {}"'.format(require, require_url))

        command = [
            './please', '-vv',
            'tools', 'deploy:S3',
            project,
            '--s3-bucket=' + deploy_options['s3_bucket'],
            '--taskcluster-secret=repo:github.com/mozilla-releng/services:branch:' + channel,
            '--no-interactive',
        ] + project_csp + project_envs + extra_attributes

    elif deploy_type == 'HEROKU':
        command = [
            './please', '-vv',
            'tools', 'deploy:HEROKU',
            project,
            '--heroku-app=' + deploy_options['heroku_app'],
            '--heroku-dyno-type=' + deploy_options['heroku_dyno_type'],
            '--taskcluster-secret=repo:github.com/mozilla-releng/services:branch:' + channel,
            '--no-interactive',
        ] + extra_attributes

    elif deploy_type == 'TASKCLUSTER_HOOK':
        command = [
            './please', '-vv',
            'tools', 'deploy:TASKCLUSTER_HOOK',
            project,
            '--hook-id=services-{}-{}'.format(channel, project),
            '--taskcluster-secret=repo:github.com/mozilla-releng/services:branch:' + channel,
            '--no-interactive',
        ] + extra_attributes
        scopes = [
          'assume:hook-id:project-releng/services-{}-*'.format(channel),
          'hooks:modify-hook:project-releng/services-{}-*'.format(channel),
        ]

    else:
        raise click.ClickException('Unknown deployment type `{}` for project `{}`'.format(deploy_type, project))

    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        channel,
        ' '.join(command),
        {
            'name': '3.{index:02}. Deploying {project}'.format(
                index=index + 1,
                project=project,
            ),
            'description': '',
            'owner': owner,
            'source': 'https://github.com/mozilla-releng/services/tree/' + channel,

        },
        scopes,
    )


def get_task(task_group_id,
             dependencies,
             github_commit,
             channel,
             command,
             metadata,
             scopes=[],
             deadline=dict(hours=5),
             max_run_time_in_hours=1,
             ):
    priority = 'high'
    if channel == 'production':
        priority = 'very-high'
    now = datetime.datetime.utcnow()
    command = (' && '.join([
      'mkdir -p /tmp/app',
      'cd /tmp/app',
      'wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 5 https://github.com/mozilla-releng/services/archive/{github_commit}.tar.gz',
      'tar zxf {github_commit}.tar.gz',
      'cd services-{github_commit}',
      'env',
      'rm -rf /home/app/.cache/nix',
      command
    ])).format(github_commit=github_commit)
    return {
        'provisionerId': 'aws-provisioner-v1',
        'workerType': 'releng-svc',
        'schedulerId': 'taskcluster-github',
        'taskGroupId': task_group_id,
        'dependencies': dependencies,
        'created': now,
        'deadline': now + datetime.timedelta(**deadline),
        'scopes': [
          'secrets:get:repo:github.com/mozilla-releng/services:branch:' + channel,
        ] + scopes,
        'priority': priority,
        'payload': {
            'maxRunTime': 60 * 60 * max_run_time_in_hours,
            'image': '{}:{}'.format(please_cli.config.DOCKER_REPO,
                                    please_cli.config.DOCKER_BASE_TAG),
            'features': {
                'taskclusterProxy': True,
            },
            'command': [
                '/bin/bash',
                '-c',
                command,
            ],
        },
        'metadata': metadata,
    }


@click.command()
@click.option(
    '--github-commit',
    envvar="GITHUB_HEAD_SHA",
    required=True,
    )
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    envvar="GITHUB_BRANCH",
    required=True,
    )
@click.option(
    '--owner',
    envvar="GITHUB_HEAD_USER_EMAIL",
    required=True,
    )
@click.option(
    '--task-id',
    envvar="TASK_ID",
    required=True,
    )
@click.option(
    '--cache-url',
    required=True,
    default=please_cli.config.CACHE_URL,
    help='Location of build artifacts.',
    )
@click.option(
    '--nix-instantiate',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-instantiate',
    help='`nix-instantiate` command',
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
    '--dry-run',
    is_flag=True,
    )
@click.pass_context
def cmd(ctx,
        github_commit,
        channel,
        owner,
        task_id,
        cache_url,
        nix_instantiate,
        taskcluster_client_id,
        taskcluster_access_token,
        dry_run,
        ):
    """A tool to be ran on each commit.
    """

    taskcluster_queue = cli_common.taskcluster.get_service('queue')

    click.echo(' => Retriving taskGroupId ... ', nl=False)
    with click_spinner.spinner():
        task = taskcluster_queue.task(task_id)

    if 'taskGroupId' not in task:
        please_cli.utils.check_result(1, 'taskGroupId does not exists in task: {}'.format(json.dumps(task)))

    task_group_id = task['taskGroupId']
    please_cli.utils.check_result(0, '')
    click.echo('    taskGroupId: ' + task_group_id)

    click.echo(' => Checking cache which project needs to be rebuilt')
    build_projects = []
    project_hashes = dict()
    for project in sorted(DEPLOYABLE_PROJECTS.keys()):
        click.echo('     => ' + project)
        project_exists_in_cache, project_hash = ctx.invoke(
            please_cli.check_cache.cmd,
            project=project,
            cache_url=cache_url,
            nix_instantiate=nix_instantiate,
            indent=8,
            interactive=False,
        )
        project_hashes[project] = project_hash
        if not project_exists_in_cache:
            build_projects.append(project)

    click.echo(' => Checking which project needs to be redeployed')
    deploy_projects = []
    if channel in please_cli.config.DEPLOY_CHANNELS:

        # TODO: get status for our index branch
        status = {}

        for project in sorted(DEPLOYABLE_PROJECTS.keys()):
            project_hash = status.get(project)

            if project_hash == project_hashes[project]:
                continue

            if channel not in DEPLOYABLE_PROJECTS[project].get('deploy_options', {}):
                continue

            deploy_projects.append(project)

    click.echo(' => Creating taskcluster tasks definitions')
    tasks = []

    # 1. build tasks
    build_tasks = {}
    for index, project in enumerate(sorted(build_projects)):
        project_uuid = slugid.nice().decode('utf-8')
        build_tasks[project_uuid] = get_build_task(
            index,
            project,
            task_group_id,
            task_id,
            github_commit,
            owner,
            channel,
        )
        tasks.append((project_uuid, build_tasks[project_uuid]))

    if deploy_projects:

        # 2. maintanance on task
        maintanance_on_uuid = slugid.nice().decode('utf-8')
        if len(build_tasks.keys()) == 0:
            maintanance_on_dependencies = [task_id]
        else:
            maintanance_on_dependencies = [i for i in build_tasks.keys()]
        maintanance_on_task = get_task(
            task_group_id,
            maintanance_on_dependencies,
            github_commit,
            channel,
            './please -vv tools maintanance:on ' + ' '.join(deploy_projects),
            {
                'name': '2. Maintanance ON',
                'description': '',
                'owner': owner,
                'source': 'https://github.com/mozilla-releng/services/tree/' + channel,

            },
        )
        tasks.append((maintanance_on_uuid, maintanance_on_task))

        # 3. deploy tasks (if on production/staging)
        deploy_tasks = {}
        for index, project in enumerate(sorted(deploy_projects)):
            project_uuid = slugid.nice().decode('utf-8')
            project_task = get_deploy_task(
                index,
                project,
                task_group_id,
                maintanance_on_uuid,
                github_commit,
                owner,
                channel,
            )
            if project_task:
                deploy_tasks[project_uuid] = project_task
                tasks.append((project_uuid, deploy_tasks[project_uuid]))

        # 4. maintanance off task
        maintanance_off_uuid = slugid.nice().decode('utf-8')
        maintanance_off_task = get_task(
            task_group_id,
            [i for i in deploy_tasks.keys()],
            github_commit,
            channel,
            './please -vv tools maintanance:off ' + ' '.join(deploy_projects),
            {
                'name': '4. Maintanance OFF',
                'description': '',
                'owner': owner,
                'source': 'https://github.com/mozilla-releng/services/tree/' + channel,

            },
        )
        maintanance_off_task['requires'] = 'all-resolved'
        tasks.append((maintanance_off_uuid, maintanance_off_task))

    click.echo(' => Submitting taskcluster definitions to taskcluster')
    if dry_run:
        tasks2 = {task_id: task for task_id, task in tasks}
        for task_id, task in tasks:
            click.echo(' => %s (%s)' % (task['metadata']['name'], task_id))
            click.echo('    dependencies:')
            for dep in task['dependencies']:
                depName = "0. Decision task"
                if dep in tasks2:
                    depName = tasks2[dep]['metadata']['name']
                click.echo('      - %s (%s)' % (depName, dep))
    else:
        for task_id, task in tasks:
            taskcluster_queue.createTask(task_id, task)


if __name__ == "__main__":
    cmd()
