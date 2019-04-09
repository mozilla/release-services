# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import functools
import json
import multiprocessing
import os
import typing

import aiohttp
import click
import click_spinner
import slugid
import tqdm

import cli_common.taskcluster
import please_cli.config
import please_cli.utils

PROJECTS = list(set(please_cli.config.PROJECTS) - set(please_cli.config.DEV_PROJECTS))
log = cli_common.log.get_logger(__name__)


def coroutine(f):
    '''A generic function to create a main asyncio loop
    '''
    coroutine_f = asyncio.coroutine(f)

    @functools.wraps(coroutine_f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine_f(*args, **kwargs))

    return wrapper


def get_build_task(index,
                   project,
                   task_group_id,
                   parent_task,
                   github_commit,
                   owner,
                   channel,
                   taskcluster_secret,
                   cache_bucket=None,
                   cache_region=None,
                   ):

    command = [
        './please', '-vv', 'tools', 'build', project,
        '--taskcluster-secret=' + taskcluster_secret,
        '--no-interactive',
        '--task-group-id', task_group_id,
        '--github-commit', github_commit,
    ]

    nix_path_attributes = [project]
    deployments = please_cli.config.PROJECTS_CONFIG[project].get('deploys', [])
    for deployment in deployments:
        for channel in deployment['options']:
            if 'nix_path_attribute' in deployment['options'][channel]:
                nix_path_attributes.append('{}.{}'.format(
                    project,
                    deployment['options'][channel]['nix_path_attribute'],
                ))
    nix_path_attributes = list(set(nix_path_attributes))

    for nix_path_attribute in nix_path_attributes:
        command.append(f'--nix-path-attribute={nix_path_attribute}')

    if cache_bucket and cache_region:
        command += [
            f'--cache-bucket={cache_bucket}',
            f'--cache-region={cache_region}',
        ]
    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        channel,
        taskcluster_secret,
        ' '.join(command),
        {
            'name': '1.{index:02}. Building {project}'.format(
                index=index + 1,
                project=project,
            ),
            'description': '',
            'owner': owner,
            'source': 'https://github.com/mozilla/release-services/tree/' + channel,

        },
        max_run_time_in_hours=5,
    )


def get_deploy_task(index,
                    project,
                    project_requires,
                    deploy_target,
                    deploy_options,
                    task_group_id,
                    parent_task,
                    github_commit,
                    owner,
                    channel,
                    taskcluster_secret,
                    ):

    scopes = []

    nix_path_attribute = deploy_options.get('nix_path_attribute')
    if nix_path_attribute:
        nix_path_attribute = '{}.{}'.format(project, nix_path_attribute)
    else:
        nix_path_attribute = project

    if deploy_target == 'S3':
        subfolder = []
        if 'subfolder' in deploy_options:
            subfolder = [deploy_options['subfolder']]
        project_csp = []
        for url in deploy_options.get('csp', []):
            project_csp.append(f'--csp="{url}"')
        for require in project_requires:
            require_config = please_cli.config.PROJECTS_CONFIG.get(require, {})

            require_urls = [
                i.get('options', {}).get(channel, {}).get('url')
                for i in require_config.get('deploys', [])
            ]
            require_urls = filter(lambda x: x is not None, require_urls)
            require_urls = map(lambda x: '--csp="{}"'.format(x), require_urls)

            project_csp += require_urls

        project_envs = []
        project_envs.append('--env="release-version: {}"'.format(please_cli.config.VERSION))
        project_envs.append('--env="release-channel: {}"'.format(channel))
        for env_name, env_value in deploy_options.get('envs', {}).items():
            project_envs.append('--env="{}: {}"'.format(env_name, env_value))
        for require in project_requires:
            require_config = please_cli.config.PROJECTS_CONFIG.get(require, {})

            require_urls = [
                (
                    i.get('options', {}).get(channel, {}).get('url'),
                    i.get('options', {}).get(channel, {}).get('name-suffix', ''),
                )
                for i in require_config.get('deploys', [])
            ]
            require_urls = filter(lambda x: x[0] is not None, require_urls)
            normalized_require = please_cli.utils.normalize_name(require, normalizer='-')
            require_urls = map(lambda x: f'--env="{normalized_require}{x[1]}-url: {x[0]}"', require_urls)

            project_envs += require_urls

        project_name = '{}{} to AWS S3 ({})'.format(
            project,
            ' ({})'.format(nix_path_attribute),
            deploy_options['s3_bucket'],
        )
        command = [
            './please', '-vv',
            'tools', 'deploy:S3',
            project,
            '--s3-bucket=' + deploy_options['s3_bucket'],
            '--taskcluster-secret=' + taskcluster_secret,
            '--nix-path-attribute=' + nix_path_attribute,
            '--no-interactive',
        ] + subfolder + project_csp + project_envs

    elif deploy_target == 'HEROKU':
        project_name = '{}{} to HEROKU ({}/{})'.format(
            project,
            ' ({})'.format(nix_path_attribute),
            deploy_options['heroku_app'],
            deploy_options['heroku_dyno_type'],
        )
        command = [
            './please', '-vv',
            'tools', 'deploy:HEROKU',
            project,
            '--heroku-app=' + deploy_options['heroku_app'],
            '--heroku-dyno-type=' + deploy_options['heroku_dyno_type'],
        ]

        heroku_command = deploy_options.get('heroku_command')
        if heroku_command:
            command.append(f'--heroku-command="{heroku_command}"')

        command += [
            '--taskcluster-secret=' + taskcluster_secret,
            '--nix-path-attribute=' + nix_path_attribute,
            '--no-interactive',
        ]

    elif deploy_target == 'DOCKERHUB':
        try:
            docker_registry = deploy_options['docker_registry']
            docker_repo = deploy_options['docker_repo']
            docker_stable_tag = deploy_options['docker_stable_tag']
        except KeyError:
            raise click.ClickException(
                'Missing `docker_registry` or `docker_repo` or `docker_stable_tag` in deploy options')

        project_name = (
            f'{project} ({nix_path_attribute}) to DOCKERHUB '
            f'({docker_registry}/{docker_repo}:{project}-{nix_path_attribute}-{channel})'
        )
        command = [
            './please', '-vv', 'tools', 'deploy:DOCKERHUB', project,
            f'--taskcluster-secret={taskcluster_secret}',
            f'--nix-path-attribute={nix_path_attribute}',
            f'--docker-repo={docker_repo}',
            f'--docker-registry={docker_registry}',
            f'--channel={channel}',
            f'--docker-stable-tag={docker_stable_tag}',
            '--no-interactive',
        ]

    elif deploy_target == 'TASKCLUSTER_HOOK':
        try:
            docker_registry = deploy_options['docker_registry']
            docker_repo = deploy_options['docker_repo']
            docker_stable_tag = deploy_options.get('docker_stable_tag')
        except KeyError:
            raise click.ClickException('Missing `docker_registry` or `docker_repo` in deploy options')
        hook_group_id = 'project-releng'
        name_suffix = deploy_options.get('name-suffix', '')
        hook_id = f'services-{channel}-{project}{name_suffix}'
        project_name = f'{project} ({nix_path_attribute}) to TASKCLUSTER HOOK ({hook_group_id}/{hook_id})'
        command = [
            './please', '-vv',
            'tools', 'deploy:TASKCLUSTER_HOOK',
            project,
            f'--docker-registry={docker_registry}',
            f'--docker-repo={docker_repo}',
            f'--hook-group-id={hook_group_id}',
            f'--hook-id={hook_id}',
            f'--taskcluster-secret={taskcluster_secret}',
            f'--nix-path-attribute={nix_path_attribute}',
            '--no-interactive',
        ]
        if docker_stable_tag is not None:
            command.append(f'--docker-stable-tag={docker_stable_tag}')
        scopes += [
          f'assume:hook-id:project-releng/services-{channel}-*',
          f'hooks:modify-hook:project-releng/services-{channel}-*',
        ]

    else:
        raise click.ClickException(f'Unknown deployment target `{deploy_target}` for project `{project}`')

    return get_task(
        task_group_id,
        [parent_task],
        github_commit,
        channel,
        taskcluster_secret,
        ' '.join(command),
        {
            'name': '3.{index:02}. Deploying {project_name}'.format(
                index=index + 1,
                project_name=project_name,
            ),
            'description': '',
            'owner': owner,
            'source': 'https://github.com/mozilla/release-services/tree/' + channel,

        },
        scopes,
    )


def get_task(task_group_id,
             dependencies,
             github_commit,
             channel,
             taskcluster_secret,
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
      # debug
      'ls -la /etc/services',
      'env',
      # cleanup
      'rm -rf /home/app/.cache/nix',
      # setup
      'source /etc/nix/profile.sh',
      'mkdir -p /tmp/app',
      'cd /tmp/app',
      'wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 5 https://github.com/mozilla/release-services/archive/{github_commit}.tar.gz',
      'tar zxf {github_commit}.tar.gz',
      'cd release-services-{github_commit}',
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
          'secrets:get:' + taskcluster_secret,
          'docker-worker:capability:privileged',
        ] + scopes,
        'priority': priority,
        'payload': {
            'maxRunTime': 60 * 60 * max_run_time_in_hours,
            'image': '{}:{}'.format(please_cli.config.DOCKER_BASE_REPO,
                                    please_cli.config.DOCKER_BASE_TAG),
            'features': {
                'taskclusterProxy': True,
            },
            'capabilities': {
                'privileged': True,
            },
            'env': {
                'GITHUB_COMMIT': github_commit,
                'TASK_GROUP_ID': task_group_id,
            },
            'command': [
                '/bin/bash',
                '-c',
                command,
            ],
        },
        'metadata': metadata,
    }


NixPath = str
NixHash = str
NixHashes = typing.List[typing.Tuple[NixPath, NixHash]]
# TODO: we need to have more detailed type for Projects but we would need to
#       have a type for please_cli.config.PROJECTS_CONFIG before that
Projects = typing.Dict


async def read_stream(stream,
                      log_output: typing.Optional[typing.Callable[[str], None]] = None,
                      callback: typing.Optional[typing.Callable[[str], None]] = None,
                      ) -> str:
    output = []
    while True:
        line = await stream.readline()
        if line:
            line = line.decode().rstrip('\n')
            if log_output:
                log_output(line)
            output.append(line)
            if callback:
                callback(line)
        else:
            break
    return '\n'.join(output)


async def run(_command: typing.Union[str, typing.List[str]],
              semaphore: typing.Optional[asyncio.Semaphore] = None,
              stream: bool = False,
              handle_stream_line: typing.Optional[typing.Callable[[str], None]] = None,
              log_command: bool = True,
              log_output: bool = True,
              secrets: typing.List[str] = [],
              **kwargs,
              ) -> typing.Tuple[int, str, str]:

    hide_secrets = cli_common.command.hide_secrets

    command: str
    if isinstance(_command, str):
        command = _command
    else:
        command = ' ' .join(_command)

    if len(command) == 0:
        raise click.ClickException('Can\'t run an empty command.')

    _kwargs = dict(
        stdin=asyncio.subprocess.DEVNULL,  # no interactions
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _kwargs.update(kwargs)

    if log_command:
        log.debug('Running command', command=hide_secrets(command, secrets), kwargs=_kwargs)

    if semaphore is None:
        process = await asyncio.create_subprocess_shell(command, **_kwargs)  # noqa
    else:
        async with semaphore:
            process = await asyncio.create_subprocess_shell(command, **_kwargs)  # noqa

    if stream:
        _log_output: typing.Optional[typing.Callable[[str], None]] = None
        if log_output:
            def _log_output(line):
                log.debug(hide_secrets(line, secrets))

        streams = []
        if process.stdout:
            streams.append(read_stream(process.stdout, _log_output, handle_stream_line))
        if process.stderr:
            streams.append(read_stream(process.stderr, _log_output, handle_stream_line))

        output, error = await asyncio.gather(*streams)
    else:
        output, error = await process.communicate()

    return process.returncode, output, error


async def check_in_nix_cache(session: aiohttp.ClientSession,
                             nix_path: NixPath,
                             nix_hash: NixHash,
                             ) -> typing.Tuple[NixPath, bool]:
    exists = False
    for cache_url in please_cli.config.CACHE_URLS:
        try:
            url = f'{cache_url}/{nix_hash}.narinfo'
            async with session.get(url) as resp:
                exists = resp.status == 200
                break
        except Exception:
            exists = False

    return (nix_path, exists)


def get_nix_paths(projects: Projects) -> typing.List[NixPath]:
    nix_paths = []
    for project, project_config in projects.items():
        nix_paths.append(project)
        deploys = project_config.get('deploys', [])
        for deploy in deploys:
            for _channel, options in deploy.get('options', dict()).items():
                if _channel not in please_cli.config.DEPLOY_CHANNELS:
                    continue
                nix_path = options.get('nix_path_attribute')
                if nix_path:
                    nix_paths.append(project + '.' + nix_path)
                else:
                    nix_paths.append(project)
    return list(set(nix_paths))


class Derive:
    '''Just out of coincidence a format of derivation is compatible with python
       which means we can evaluate it.
    '''
    def __init__(self, *drv):
        self._drv = drv

    @property
    def nix_hash(self):
        '''We are only interested into nix_hash, which we need to parse from
           derivation structure.
        '''
        return self._drv[0][0][1][11:43]


async def get_projects_hash(semaphore: asyncio.Semaphore,
                            nix_instantiate: str,
                            nix_path: NixPath):
    default_nix = os.path.join(please_cli.config.ROOT_DIR, 'nix/default.nix')
    code, output, error = await run([nix_instantiate, default_nix, '-A', nix_path],
                                    stream=True,
                                    semaphore=semaphore,
                                    )
    try:
        drv_path = output.split('\n')[-1].strip()
        with open(drv_path) as f:
            drv = eval(f.read())
    except Exception as e:
        log.exception(e)
        raise click.ClickException(
            'Something went wrong when reading derivation file for '
            '`{}` project.'.format(nix_path))
    return (nix_path, drv.nix_hash)


async def get_projects_hashes(nix_instantiate: str,
                              projects: Projects,
                              ) -> NixHashes:
    # this limits nix calls allowed to make at the same time
    semaphore = asyncio.Semaphore(value=multiprocessing.cpu_count())

    nix_hashes = []
    tasks = [
        get_projects_hash(semaphore, nix_instantiate, nix_path)
        for nix_path in get_nix_paths(projects)
    ]
    for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        nix_hashes.append(await task)
    return nix_hashes


def nix_path_to_project(nix_path: NixPath) -> str:
    return nix_path.split('.')[0]


async def get_projects_to_build(session: aiohttp.ClientSession,
                                projects: Projects,
                                nix_hashes: NixHashes
                                ) -> typing.List[str]:

    project_to_build: typing.Dict[str, bool] = dict()
    tasks = [
        check_in_nix_cache(session, nix_path, nix_hash)
        for nix_path, nix_hash in nix_hashes
    ]
    for task in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        nix_path, exists = await task
        project = nix_path_to_project(nix_path)
        current_exists = project_to_build.get(project, True)
        if current_exists is False:
            continue
        project_to_build[project] = exists
    return [
        project
        for project, exists in project_to_build.items()
        if exists
    ]


@click.command()
@click.option(
    '--github-commit',
    envvar='GITHUB_HEAD_SHA',
    required=True,
    )
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    envvar='GITHUB_BRANCH',
    required=True,
    )
@click.option(
    '--owner',
    envvar='GITHUB_HEAD_USER_EMAIL',
    required=True,
    )
@click.option(
    '--pull-request',
    envvar='GITHUB_PULL_REQUEST',
    default=None,
    required=False,
    )
@click.option(
    '--task-id',
    envvar='TASK_ID',
    required=True,
    )
@click.option(
    '--cache-url',
    'cache_urls',
    multiple=True,
    default=please_cli.config.CACHE_URLS,
    help='Locations of build artifacts.',
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
@coroutine
async def cmd(ctx,
              github_commit,
              channel,
              owner,
              pull_request,
              task_id,
              cache_urls,
              nix_instantiate,
              taskcluster_client_id,
              taskcluster_access_token,
              dry_run,
              ):
    '''A tool to be ran on each commit.
    '''

    taskcluster_secret = 'repo:github.com/mozilla-releng/services:branch:' + channel
    if pull_request is not None:
        taskcluster_secret = 'repo:github.com/mozilla-releng/services:pull-request'

    taskcluster_queue = cli_common.taskcluster.get_service('queue', _async=True)
    taskcluster_notify = cli_common.taskcluster.get_service('notify', _async=True)

    click.echo(' => Retriving taskGroupId ... ', nl=False)
    with click_spinner.spinner():
        task = await taskcluster_queue.task(task_id)
        if 'taskGroupId' not in task:
            please_cli.utils.check_result(1, 'taskGroupId does not exists in task: {}'.format(json.dumps(task)))
        task_group_id = task['taskGroupId']
        please_cli.utils.check_result(0, '')
        click.echo('    taskGroupId: ' + task_group_id)

    if channel in please_cli.config.DEPLOY_CHANNELS and not dry_run:
        await taskcluster_notify.irc(dict(channel='#release-services',
                                          message=f'New deployment on {channel} is about to start: https://tools.taskcluster.net/groups/{task_group_id}'))

    message = ('release-services team is about to release a new version of mozilla/release-services '
               '(*.mozilla-releng.net, *.moz.tools). Any alerts coming up soon will be best directed '
               'to #release-services IRC channel. Automated message (such as this) will be send '
               'once deployment is done. Thank you.')

    # This message will only be sent when channel is production.
    if channel == 'production' and not dry_run:
        for msgChannel in ['#ci', '#moc']:
            await taskcluster_notify.irc(dict(channel=msgChannel, message=message))

    projects = {
        project: please_cli.config.PROJECTS_CONFIG.get(project, {})
        for project in PROJECTS
    }

    click.echo(' => Checking for project\'s Nix hashes')
    nix_hashes = await get_projects_hashes(nix_instantiate, projects)

    click.echo(' => Checking if project\'s Nix hashes exists in cache')

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=50)) as session:
        build_projects = await get_projects_to_build(session, projects, nix_hashes)

    projects_to_deploy = []

    if channel in please_cli.config.DEPLOY_CHANNELS:
        click.echo(' => Checking which project needs to be redeployed')

        for project_name in sorted(PROJECTS):

            # update hook for each project
            if please_cli.config.PROJECTS_CONFIG[project_name]['update'] is True:

                if channel == 'production':
                    update_hook_nix_path_atttribute = f'updateHook.{channel}.scheduled'
                else:
                    update_hook_nix_path_atttribute = f'updateHook.{channel}.notScheduled'

                projects_to_deploy.append((
                    project_name,
                    [],
                    'TASKCLUSTER_HOOK',
                    {
                        'enable': True,
                        'docker_registry': 'index.docker.io',
                        'docker_repo': 'mozillareleng/services',
                        'name-suffix': '-update-dependencies',
                        'nix_path_attribute': update_hook_nix_path_atttribute,
                    },
                ))

            if 'deploys' not in please_cli.config.PROJECTS_CONFIG[project_name]:
                continue

            for deploy in please_cli.config.PROJECTS_CONFIG[project_name]['deploys']:
                for deploy_channel in deploy['options']:
                    if channel == deploy_channel:
                        projects_to_deploy.append((
                            project_name,
                            please_cli.config.PROJECTS_CONFIG[project_name].get('requires', []),
                            deploy['target'],
                            deploy['options'][channel],
                        ))

    click.echo(' => Creating taskcluster tasks definitions')
    tasks = []

    # 1. build tasks
    build_tasks = {}
    for index, project in enumerate(sorted(build_projects)):
        project_uuid = slugid.nice()
        required = []
        if pull_request is not None:
            required += [
                'CACHE_BUCKET',
                'CACHE_REGION',
            ]
        secrets = cli_common.taskcluster.get_secrets(
            taskcluster_secret,
            project,
            required=required,
            taskcluster_client_id=taskcluster_client_id,
            taskcluster_access_token=taskcluster_access_token,
        )
        build_tasks[project_uuid] = get_build_task(
            index,
            project,
            task_group_id,
            task_id,
            github_commit,
            owner,
            channel,
            taskcluster_secret,
            pull_request is None and secrets.get('CACHE_BUCKET') or None,
            pull_request is None and secrets.get('CACHE_REGION') or None,
        )
        tasks.append((project_uuid, build_tasks[project_uuid]))

    if projects_to_deploy:

        # 2. maintanance on task
        maintanance_on_uuid = slugid.nice()
        if len(build_tasks.keys()) == 0:
            maintanance_on_dependencies = [task_id]
        else:
            maintanance_on_dependencies = [i for i in build_tasks.keys()]
        maintanance_on_task = get_task(
            task_group_id,
            maintanance_on_dependencies,
            github_commit,
            channel,
            taskcluster_secret,
            './please -vv tools maintanance:on ' + ' '.join(list(set([i[0] for i in projects_to_deploy]))),
            {
                'name': '2. Maintanance ON',
                'description': '',
                'owner': owner,
                'source': 'https://github.com/mozilla/release-services/tree/' + channel,

            },
        )
        tasks.append((maintanance_on_uuid, maintanance_on_task))

        # 3. deploy tasks (if on production/staging)
        deploy_tasks = {}
        for index, (project, project_requires, deploy_target, deploy_options) in \
                enumerate(sorted(projects_to_deploy, key=lambda x: x[0])):
            try:
                enable = deploy_options['enable']
            except KeyError:
                raise click.ClickException(f'Missing {enable} in project {project} and channel {channel} deploy options')

            if not enable:
                continue

            project_uuid = slugid.nice()
            project_task = get_deploy_task(
                index,
                project,
                project_requires,
                deploy_target,
                deploy_options,
                task_group_id,
                maintanance_on_uuid,
                github_commit,
                owner,
                channel,
                taskcluster_secret,
            )
            if project_task:
                deploy_tasks[project_uuid] = project_task
                tasks.append((project_uuid, deploy_tasks[project_uuid]))

        # 4. maintanance off task
        maintanance_off_uuid = slugid.nice()
        maintanance_off_task = get_task(
            task_group_id,
            [i for i in deploy_tasks.keys()],
            github_commit,
            channel,
            taskcluster_secret,
            './please -vv tools maintanance:off ' + ' '.join(list(set([i[0] for i in projects_to_deploy]))),
            {
                'name': '4. Maintanance OFF',
                'description': '',
                'owner': owner,
                'source': 'https://github.com/mozilla/release-services/tree/' + channel,

            },
        )
        maintanance_off_task['requires'] = 'all-resolved'
        tasks.append((maintanance_off_uuid, maintanance_off_task))

    click.echo(' => Submitting taskcluster definitions to taskcluster')
    if dry_run:
        tasks2 = {task_id: task for task_id, task in tasks}
        for task_id, task in tasks:
            click.echo(' => %s [taskId: %s]' % (task['metadata']['name'], task_id))
            click.echo('    dependencies:')
            deps = []
            for dep in task['dependencies']:
                depName = '0. Decision task'
                if dep in tasks2:
                    depName = tasks2[dep]['metadata']['name']
                    deps.append('      - %s [taskId: %s]' % (depName, dep))
            for dep in sorted(deps):
                click.echo(dep)
    else:
        for task_id, task in tasks:
            await taskcluster_queue.createTask(task_id, task)


if __name__ == '__main__':
    cmd()
