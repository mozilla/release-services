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


DEPLOYABLE_APPS = {}
for app_name, app_config in please_cli.config.APPS.items():
    if 'deploy' in app_config:
        DEPLOYABLE_APPS[app_name] = app_config


def get_build_task(index,
                   app,
                   task_group_id,
                   parent_task,
                   github_commit,
                   github_branch,
                   github_user_email,
                   ):
    command = [
        './please', '-vv', 'tools', 'build', app,
        '--cache-bucket="releng-cache"',
        '--extra-attribute="{}.deploy.{}"'.format(app, github_branch),
        '--taskcluster-secrets=repo:github.com/mozilla-releng/services:branch:' + github_branch,
        '--no-interactive',
    ]
    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        github_branch,
        ' '.join(command),
        {
            'name': '1.{index:02}. Building {app}'.format(
                index=index + 1,
                app=app,
            ),
            'description': '',
            'owner': github_user_email,
            'source': 'https://github.com/mozilla-releng/services/tree/' + github_branch,

        },
        max_run_time_in_hours=3,
    )


def get_deploy_task(index,
                    app,
                    task_group_id,
                    parent_task,
                    github_commit,
                    github_branch,
                    github_user_email,
                    ):

    app_config = please_cli.config.APPS.get(app, {})
    deploy_type = app_config.get('deploy')
    deploy_options = app_config.get('deploy_options', {}).get(github_branch, {})
    scopes = []

    if deploy_type == 'S3':
        app_csp = []
        for url in deploy_options.get('csp', []):
            app_csp.append('--csp="{}"'.format(url))
        for require in app_config.get('requires', []):
            require_config = please_cli.config.APPS.get(require, {})
            require_deploy_options = require_config.get('deploy_options', {}).get(github_branch, {})
            require_url = require_deploy_options.get('url')
            if require_url:
                app_csp.append('--csp="{}"'.format(require_url))

        app_envs = []
        for env_name, env_value in deploy_options.get('envs', {}).items():
            app_envs.append('--env="{}: {}"'.format(env_name, env_value))
        for require in app_config.get('requires', []):
            require_config = please_cli.config.APPS.get(require, {})
            require_deploy_options = require_config.get('deploy_options', {}).get(github_branch, {})
            require_url = require_deploy_options.get('url')
            if require_url:
                env_name = '-'.join(require.split('-')[1:])
                app_envs.append('--env="{}-url: {}"'.format(env_name, require_url))

        command = [
            './please', '-vv',
            'tools', 'deploy:S3',
            app,
            '--s3-bucket=' + deploy_options['s3_bucket'],
            '--extra-attribute="{}.deploy.{}"'.format(app, github_branch),
            '--taskcluster-secrets=repo:github.com/mozilla-releng/services:branch:' + github_branch,
            '--no-interactive',
        ] + app_csp + app_envs

    elif deploy_type == 'HEROKU':
        command = [
            './please', '-vv',
            'tools', 'deploy:HEROKU',
            app,
            '--heroku-app=' + deploy_options['heroku_app'],
            '--extra-attribute="{}.deploy.{}"'.format(app, github_branch),
            '--taskcluster-secrets=repo:github.com/mozilla-releng/services:branch:' + github_branch,
            '--no-interactive',
        ]

    elif deploy_type == 'TASKCLUSTER_HOOK':
        command = [
            './please', '-vv',
            'tools', 'deploy:TASKCLUSTER_HOOK',
            app,
            '--hook-id=services-{}-{}'.format(github_branch, app),
            '--extra-attribute="{}.deploy.{}"'.format(app, github_branch),
            '--taskcluster-secrets=repo:github.com/mozilla-releng/services:branch:' + github_branch,
            '--no-interactive',
        ]
        scopes = [
          'assume:hook-id:project-releng/services-{}-*'.format(github_branch),
          'hooks:modify-hook:project-releng/services-{}-*'.format(github_branch),
        ]

    else:
        raise click.ClickException('Unknown deployment type `{}` for application `{}`'.format(deploy_type, app))

    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        github_branch,
        ' '.join(command),
        {
            'name': '3.{index:02}. Deploying {app}'.format(
                index=index + 1,
                app=app,
            ),
            'description': '',
            'owner': github_user_email,
            'source': 'https://github.com/mozilla-releng/services/tree/' + github_branch,

        },
        scopes,
    )


def get_task(task_group_id,
             dependencies,
             github_commit,
             github_branch,
             command,
             metadata,
             scopes=[],
             deadline=dict(hours=5),
             max_run_time_in_hours=1,
             ):
    now = datetime.datetime.utcnow()
    command = (' && '.join([
      'cd /tmp',
      'wget https://github.com/mozilla-releng/services/archive/{github_commit}.tar.gz',  # noqa
      'tar zxf {github_commit}.tar.gz',
      'cd services-{github_commit}',
      'env',
      'rm -rf /root/.cache/nix',
      command
    ])).format(
        github_branch=github_branch,
        github_commit=github_commit,
    )
    return {
        'provisionerId': 'aws-provisioner-v1',
        'workerType': 'releng-task',
        'schedulerId': 'taskcluster-github',
        'taskGroupId': task_group_id,
        'dependencies': dependencies,
        'created': now,
        'deadline': now + datetime.timedelta(**deadline),
        'scopes': [
          'secrets:get:repo:github.com/mozilla-releng/services:branch:' + github_branch,
        ] + scopes,
        'payload': {
            'maxRunTime': 60 * 60 * max_run_time_in_hours,
            'image': 'mozillareleng/services:base-latest',
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
    '--github-branch',
    envvar="GITHUB_HEAD_BRANCH",
    required=True,
    )
@click.option(
    '--github-user-email',
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
        github_branch,
        github_user_email,
        task_id,
        cache_url,
        nix_instantiate,
        taskcluster_client_id,
        taskcluster_access_token,
        dry_run,
        ):
    """A tool to be ran on each commit.
    """

    taskcluster = cli_common.taskcluster.TaskclusterClient(
        taskcluster_client_id,
        taskcluster_access_token,
    )
    taskcluster_queue = taskcluster.get_service('queue')

    click.echo(' => Retriving taskGroupId ... ', nl=False)
    with click_spinner.spinner():
        task = taskcluster_queue.task(task_id)

    if 'taskGroupId' not in task:
        please_cli.utils.check_result(1, 'taskGroupId does not exists in task: {}'.format(json.dumps(task)))

    task_group_id = task['taskGroupId']
    please_cli.utils.check_result(0, '')
    click.echo('    taskGroupId: ' + task_group_id)

    click.echo(' => Checking cache which application needs to be rebuilt')
    build_apps = []
    app_hashes = dict()
    for app in sorted(DEPLOYABLE_APPS.keys()):
        click.echo('     => ' + app)
        app_exists_in_cache, app_hash = ctx.invoke(
            please_cli.check_cache.cmd,
            app=app,
            cache_url=cache_url,
            nix_instantiate=nix_instantiate,
            indent=8,
            interactive=False,
        )
        app_hashes[app] = app_hash
        if not app_exists_in_cache:
            build_apps.append(app)

    click.echo(' => Checking which application needs to be redeployed')
    deploy_apps = []
    if github_branch in please_cli.config.DEPLOYMENT_BRANCHES:

        # TODO: get status for our index branch
        status = {}

        for app in sorted(DEPLOYABLE_APPS.keys()):
            app_hash = status.get(app)

            if app_hash == app_hashes[app]:
                continue

            if github_branch not in DEPLOYABLE_APPS[app].get('deploy_options', {}):
                continue

            deploy_apps.append(app)

    click.echo(' => Creating taskcluster tasks definitions')
    tasks = []

    # 1. build tasks
    build_tasks = {}
    for index, app in enumerate(sorted(build_apps)):
        app_uuid = slugid.nice().decode('utf-8')
        build_tasks[app_uuid] = get_build_task(
            index,
            app,
            task_group_id,
            task_id,
            github_commit,
            github_branch,
            github_user_email,
        )
        tasks.append((app_uuid, build_tasks[app_uuid]))

    if deploy_apps:

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
            github_branch,
            './please -vv tools maintanance:on ' + ' '.join(deploy_apps),
            {
                'name': '2. Maintanance ON',
                'description': '',
                'owner': github_user_email,
                'source': 'https://github.com/mozilla-releng/services/tree/' + github_branch,

            },
        )
        tasks.append((maintanance_on_uuid, maintanance_on_task))

        # 3. deploy tasks (if on production/staging)
        deploy_tasks = {}
        for index, app in enumerate(sorted(deploy_apps)):
            app_uuid = slugid.nice().decode('utf-8')
            app_task = get_deploy_task(
                index,
                app,
                task_group_id,
                maintanance_on_uuid,
                github_commit,
                github_branch,
                github_user_email,
            )
            if app_task:
                deploy_tasks[app_uuid] = app_task
                tasks.append((app_uuid, deploy_tasks[app_uuid]))

        # 4. maintanance off task
        maintanance_off_uuid = slugid.nice().decode('utf-8')
        maintanance_off_task = get_task(
            task_group_id,
            [i for i in deploy_tasks.keys()],
            github_commit,
            github_branch,
            './please -vv tools maintanance:off ' + ' '.join(deploy_apps),
            {
                'name': '4. Maintanance OFF',
                'description': '',
                'owner': github_user_email,
                'source': 'https://github.com/mozilla-releng/services/tree/' + github_branch,

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
