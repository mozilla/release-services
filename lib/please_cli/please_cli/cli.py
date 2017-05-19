#!/usr/bin/env python3

import click
import copy
import click.exceptions
import json
import logging
import shlex
import subprocess
import taskcluster
import push
import requests


DOCKER_REGISTRY = "https://index.docker.com"
CACHE_URL = "https://cache.mozilla-releng.net"

log = logging.getLogger('taskcluster-cli')


def cmp(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def cmd(command):

    if isinstance(command, str):
        command = shlex.split(command)

    log.debug('COMMAND: ' + ' '.join(command))

    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        )

    out = []
    while True:
        line = p.stdout.readline().decode()
        if line == '' and p.poll() is not None:
            break
        if line != '':
            log.debug(line.rstrip('\n'))
            out.append(line)

    return p.returncode, '\n'.join(out)


def nixpath_to_tag(repo, image_path):
    if image_path.startswith('/nix/store'):
        tag = '-'.join(reversed(image_path[11:-7].split('-', 1)))
        return "%s:%s" % (repo, tag)
    return image_path


def _get_taskcluster_tool(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
        ):

    if taskcluster_base_url is None and taskcluster_client_id is None and \
           taskcluster_access_token is None:
        raise click.exceptions.ClickException(
            "You need to provide either:\n"
            "  (1) `--taskcluster-base--url`\n"
            "  (2) or both `--taskcluster-client-id` and `--taskcluster-access-token`."  # noqa
        )

    elif taskcluster_client_id and taskcluster_access_token is None:
        raise click.exceptions.ClickException(
            "You need to provide `--taskcluster-access-token` option.")

    elif taskcluster_client_id is None and taskcluster_access_token:
        raise click.exceptions.ClickException(
            "You need to provide `--taskcluster-client-id` option.")

    def __get_taskcluster_tool(name):

        options = dict()

        if taskcluster_client_id and taskcluster_access_token:
            options = dict(
                credentials=dict(
                    clientId=taskcluster_client_id,
                    accessToken=taskcluster_access_token,
                )
            )

        if taskcluster_base_url:
            options = dict(
                baseUrl=taskcluster_base_url,
            )

        name = name.lower()
        tool = getattr(
            taskcluster,
            name[0].upper() + name[1:],
        )

        if 'baseUrl' in options:
            return tool({
                **options,
                **{"baseUrl": options['baseUrl'] + ("/%s/v1" % name)},
            })
        else:
            return tool(options)

    return __get_taskcluster_tool


def _push_docker_image(
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
        ):

    def __push_docker_image(image):

        # only upload if image is create via nix
        if image.startswith('/nix/store'):

            image_path = image
            image = nixpath_to_tag(docker_repo, image_path)
            tag = image[image.find(':', 1) + 1:]

            click.echo(' => ' + image)

            push.registry.push(
                push.image.spec(image_path),
                docker_registry,
                docker_username,
                docker_password,
                docker_repo,
                tag,
            )

        return image

    return __push_docker_image


def _diff_hooks(all, existing, prefix, repo):
    create, update, remove = {}, {}, {}

    for hookId, hook in all.items():
        if hookId not in existing.keys() and hookId.startswith(prefix):
            if 'hookId' in hook:
                del hook['hookId']
            if 'hookGroupId' in hook:
                del hook['hookGroupId']
            create[hookId] = hook

    for hookId, hook in existing.items():
        if 'hookId' in hook:
            del hook['hookId']
        if 'hookGroupId' in hook:
            del hook['hookGroupId']
        if hookId in all.keys():
            tmp_hook = copy.deepcopy(all[hookId])
            tmp_hook['task']['payload']['image'] =\
                nixpath_to_tag(repo, tmp_hook['task']['payload']['image'])
            if not cmp(tmp_hook, hook):
                update[hookId] = all[hookId]
        else:
            remove[hookId] = hook

    return create, update, remove


@main.command()
@click.option('--hooks', required=True, type=click.File())
@click.option('--hooks-group', required=True)
@click.option('--hooks-prefix', required=True, default="services-")
@click.option('--hooks-url', default=None, required=False)
@click.option('--taskcluster-client-id', default=None, required=False)
@click.option('--taskcluster-access-token', default=None, required=False)
@click.option('--taskcluster-base-url', default=None, required=False)
@click.option('--docker-registry', required=False, default=DOCKER_REGISTRY)
@click.option('--docker-repo', required=True)
@click.option('--docker-username', required=True)
@click.option('--docker-password', required=True)
@click.option('--debug', is_flag=True)
def hooks(hooks,
          hooks_group,
          hooks_prefix,
          taskcluster_client_id,
          taskcluster_access_token,
          taskcluster_base_url,
          docker_registry,
          docker_repo,
          docker_username,
          docker_password,
          ):
    """ A tool for declerativly creating / removing / updating taskcluster
        hooks.
    """

    get_taskcluster_tool = _get_taskcluster_tool(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
    )

    push_docker_image = _push_docker_image(
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
    )

    taskcluster_hooks = get_taskcluster_tool('hooks')

    hooks_all = json.load(hooks)
    click.echo("Expected hooks:%s" % "\n - ".join([""] + list(hooks_all.keys())))

    log.debug("Gathering existing hooks for group `%s`. Might take some time ..." % hooks_group)
    hooks_existing = {
        hook['hookId']: hook
        for hook in taskcluster_hooks.listHooks(hooks_group).get('hooks', [])
        if hook.get('hookId', '').startswith(hooks_prefix)
    }

    click.echo("Existing hooks: %s" % "\n - ".join([""] + list(hooks_existing.keys())))

    hooks_create, hooks_update, hooks_remove = \
        _diff_hooks(hooks_all, hooks_existing, hooks_prefix, docker_repo)

    log.debug("Hooks to create:%s" % "\n - ".join([""] + list(hooks_create.keys())))
    log.debug("Hooks to update:%s" % "\n - ".join([""] + list(hooks_update.keys())))
    log.debug("Hooks to remove:%s" % "\n - ".join([""] + list(hooks_remove.keys())))

    click.echo("Pushing images to docker_registry:")

    for hookId, hook in hooks_create.items():
        image = push_docker_image(hook['task']['payload']['image'])
        hooks_create[hookId]['task']['payload']['image'] = image

    for hookId, hook in hooks_update.items():
        image = push_docker_image(hook['task']['payload']['image'])
        hooks_update[hookId]['task']['payload']['image'] = image

    click.echo("Creating new hooks:")

    for hookId, hook in hooks_create.items():
        click.echo(" - %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.createHook(hooks_group, hookId, hook)

    click.echo("Updating hooks:")

    for hookId, hook in hooks_update.items():
        click.echo(" - %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.updateHook(hooks_group, hookId, hook)

    click.echo("Removing hooks:")

    for hookId, hook in hooks_remove.items():
        click.echo(" - %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.removeHook(hooks_group, hookId)


@main.command("create-tasks-json")
@click.argument("apps", required=True, nargs=-1)
def create_tasks_json(apps):
    """A tool that creates
    """


@main.command("check-cache")
@click.option('--cache-url', required=True, default=CACHE_URL)
@click.argument("app", required=True)
def check_cache(cache_url, app):

    class Derive:
        def __init__(self, *drv):
            self._drv = drv

        @property
        def nix_hash(self):
            return self._drv[0][0][1][11:43]

    code, output = cmd('nix-instantiate nix/default.nix -A apps.' + app)
    drv = output.split('\n')[-2].strip()

    with open(drv) as f:
        derivation = eval(f.read())

    response = requests.get('%s/%s.narinfo' % (cache_url, derivation.nix_hash))
    if response.status_code == 200:
        click.echo('EXISTS')
    else:
        click.echo('NOT EXISTS')


@main.command()
@click.option('--tasks-file', required=True, type=click.File())
@click.option('--taskcluster-client-id', default=None, required=False)
@click.option('--taskcluster-access-token', default=None, required=False)
@click.option('--taskcluster-base-url', default=None, required=False)
@click.option('--docker-registry', required=False, default=DOCKER_REGISTRY)
@click.option('--docker-repo', required=True)
@click.option('--docker-username', required=True)
@click.option('--docker-password', required=True)
def tasks(taskcluster_client_id,
          taskcluster_access_token,
          taskcluster_base_url,
          docker_registry,
          docker_repo,
          docker_username,
          docker_password,
          tasks_file,
          ):
    """A tool for declerativly creating taskcluster tasks.
    """

    get_taskcluster_tool = _get_taskcluster_tool(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
    )

    push_docker_image = _push_docker_image(
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
    )

    # 1. push all images created via nix to docker registry
    tasks = json.load(tasks_file)
    for taskId, task in tasks.items():
        image = push_docker_image(task['payload']['image'])
        tasks[taskId]['payload']['image'] = image

    # 2. create taskcluster tasks
    taskcluster_queue = get_taskcluster_tool('queue')
    for taskId, task in tasks.items():
        taskcluster_queue.createTask(taskId, task)


if __name__ == "__main__":
    main()
