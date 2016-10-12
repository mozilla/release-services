#!/usr/bin/env python3

import click
import click.exceptions
import copy
import json
import logging
import shlex
import subprocess
import taskcluster


log = logging.getLogger('hooks')


def cmd(command):

    if isinstance(command, basestring):
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

def push_docker_image(image, push, registry, repo, username, password):

    # only upload if image is create via nix
    if image.startswith('/nix/store'):
        image_path = image
        image = nix_to_tag(repo, image_path)
        tag = image[image.find(':', 1) + 1:]

        click.echo(' - ' + image)
        returncode, output = cmd(
            '%s %s %s -u "%s" -p "%s" -N "%s" -T "%s"' % (
                push, image_path, registry, username, password, repo, tag))

        if returncode != 0:
            click.echo(output)
            raise click.exceptions.ClickException("Error while pushing docker images")

    return image


def diff_hooks(all, existing, prefix, repo):
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
            tmp_hook['task']['payload']['image'] = nix_to_tag(repo, tmp_hook['task']['payload']['image'])  # noqa
            if cmp(tmp_hook, hook) != 0:
                update[hookId] = all[hookId]
        else:
            remove[hookId] = hook

    return create, update, remove


@click.command()
@click.option('--hooks', required=True, type=click.File())
@click.option('--hooks-group', required=True)
@click.option('--hooks-prefix', required=True, default="services-")
@click.option('--hooks-url', default=None, required=False)
@click.option('--hooks-client-id', default=None, required=False)
@click.option('--hooks-access-token', default=None, required=False)
@click.option('--docker-push', required=True, type=click.Path(resolve_path=True))
@click.option('--docker-registry', required=True, default="https://index.docker.com")  # noqa
@click.option('--docker-repo', required=True)
@click.option('--docker-username', required=True)
@click.option('--docker-password', required=True)
@click.option('--debug', is_flag=True)
def main(hooks, hooks_group, hooks_prefix, hooks_url, hooks_client_id,
         hooks_access_token, docker_push, docker_registry, docker_repo,
         docker_username, docker_password, debug):
    """ A tool for creating / updating taskcluster hooks (also creating and
        pushing docker images.
    """

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    taskcluster_hooks = None

    if hooks_client_id is not None and hooks_access_token is not None:
        taskcluster_hooks = taskcluster.Hooks(
            options=dict(
                credentials=dict(
                    clientId=hooks_client_id,
                    accessToken=hooks_access_token,
                )
            )
        )

    if hooks_url:
        taskcluster_hooks = taskcluster.Hooks(
            options=dict(
                baseUrl=hooks_url
            )
        )

    if taskcluster_hooks is None:
        raise ClickException(
            "You either need to provide `--hooks-url` or both "
            "`--hooks-client-id` and `--hooks-access-token`."
        )

    hooks_all = json.load(hooks)
    click.echo("Expected hooks:%s" % "\n - ".join([""] + list(hooks_all.keys())))

    log.debug("Gathering existing hooks for group `%s`. Might take some time ..." % hooks_group)
    hooks_existing = {
        hook['hookId']: hook
        for hook in taskcluster_hooks.listHooks(hooks_group).get('hooks', [])
        if hook.get('hookId', '').startswith(hooks_prefix)
    }

    click.echo("Existing hooks: %s" % "\n - ".join([""] + list(hooks_existing.keys())))

    hooks_create, hooks_update, hooks_remove = diff_hooks(hooks_all,
                                                          hooks_existing,
                                                          hooks_prefix,
                                                          docker_repo,
                                                          )

    log.debug("Hooks to create:%s" % "\n - ".join([""] + list(hooks_create.keys())))
    log.debug("Hooks to update:%s" % "\n - ".join([""] + list(hooks_update.keys())))
    log.debug("Hooks to remove:%s" % "\n - ".join([""] + list(hooks_remove.keys())))

    click.echo("Pushing images to docker_registry:")

    for hookId, hook in hooks_create.items():
        hook_image = push_docker_image(
            hook['task']['payload']['image'],
            docker_push,
            docker_registry,
            docker_repo,
            docker_username,
            docker_password)
        hooks_create[hookId]['task']['payload']['image'] = hook_image

    for hookId, hook in hooks_update.items():
        hook_image = push_docker_image(
            hook['task']['payload']['image'],
            docker_push,
            docker_registry,
            docker_repo,
            docker_username,
            docker_password)
        hooks_update[hookId]['task']['payload']['image'] = hook_image

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


if __name__ == "__main__":
    main()
