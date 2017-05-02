#!/usr/bin/env python3

import click
import click.exceptions
import json
import logging
import shlex
import subprocess
import taskcluster
import push


log = logging.getLogger('taskcluster-tasks')


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


def nix_to_tag(repo, image_path):
    if image_path.startswith('/nix/store'):
        tag = '-'.join(reversed(image_path[11:-7].split('-', 1)))
        return "%s:%s" % (repo, tag)
    return image_path


def _get_tool(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
        ):

    def __get_tool(name):

        if taskcluster_base_url is None and taskcluster_client_id is None and \
               taskcluster_access_token is None:
            raise click.exceptions.ClickException(
                "You need to provide either:\n  (1) `--taskcluster-base--url`"
                "\n  (2) or both `--taskcluster-client-id` and "
                "`--taskcluster-access-token`."
            )

        if taskcluster_client_id and taskcluster_access_token is None:
            raise click.exceptions.ClickException(
                "You need to provide `--taskcluster-access-token` option.")
        elif taskcluster_client_id is None and taskcluster_access_token:
            raise click.exceptions.ClickException(
                "You need to provide `--taskcluster-client-id` option.")

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
        import pdb
        pdb.set_trace()

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

    return __get_tool


def _push_image(
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
        ):

    def __push_image(image):

        # only upload if image is create via nix
        if image.startswith('/nix/store'):

            image_path = image
            image = nix_to_tag(docker_repo, image_path)
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

    return __push_image


@click.command('taskcluster-tasks')
@click.option('--taskcluster-client-id', default=None, required=False)
@click.option('--taskcluster-access-token', default=None, required=False)
@click.option('--taskcluster-base-url', default=None, required=False)
@click.option('--docker-registry', required=False, default="https://index.docker.com")  # noqa
@click.option('--docker-repo', required=False)
@click.option('--docker-username', required=False)
@click.option('--docker-password', required=False)
@click.option('--tasks-file', required=True, type=click.File())
@click.option('--debug', is_flag=False)
def main(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
        tasks_file,
        debug,
        ):

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    get_tool = _get_tool(
        taskcluster_client_id,
        taskcluster_access_token,
        taskcluster_base_url,
    )

    push_image = _push_image(
        docker_registry,
        docker_repo,
        docker_username,
        docker_password,
    )

    # 1. push all images to docker registry
    tasks = json.load(tasks_file)
    for taskId, task in tasks.items():
        image = push_image(task['payload']['image'])
        tasks[taskId]['payload']['image'] = image

    # 2. create taskcluster tasks
    queue = get_tool('queue')
    for taskId, task in tasks.items():
        from pprint import pprint
        pprint(task)
        queue.createTask(taskId, task)


if __name__ == "__main__":
    main()
