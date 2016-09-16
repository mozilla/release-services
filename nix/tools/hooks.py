
import json
import click
import taskcluster
import logging
import shlex
import subprocess


log = logging.getLogger('hooks')


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


def push_docker_image(image, push, registry, repo, username, password):

    # only upload if image is create via nix
    if image.startswith('/nix/store'):
        image_path = image

        tag = '-'.join(reversed(image_path[11:-7].split('-', 1)))
        image = "%s:%s" % (repo, tag)

        # TODO: check if image (tag) is already uploaded
        returncode, output = cmd(
            '%s %s %s -u "%s" -p "%s" -N "%s" -T "%s"" % (
                push, image_path, registry, username, password, repo, tag))

        import ipdb
        ipdb.set_trace()
    return image


def diff_hooks(all, existing, prefix):
    create, update, remove = {}, {}, {}

    for hookId, hook in all.items():
        if hookId not in existing.keys() and hookId.startswith(prefix):
            if 'hookId' in hook:
                del hook['hookId']
            if 'hookGroupId' in hook:
                del hook['hookGroupId']
            create[hookId] = hook

    for hookId, hook in existing.items():
        if hookId in all.keys():
            # TODO: check if update is really needed
            update[hookId] = all[hookId]
        else:
            remove[hookId] = hook

    return create, update, remove


@click.command()
@click.option('--hooks', required=True, type=click.File())
@click.option('--hooks-group', required=True)
@click.option('--hooks-prefix', required=True, default="services-")
@click.option('--hooks-client-id', required=True)
@click.option('--hooks-access-token', required=True)
@click.option('--docker-push', required=True, type=click.Path())
@click.option('--docker-registry', required=True, default="https://index.docker.com")  # noqa
@click.option('--docker-repo', required=True)
@click.option('--docker-username', required=True)
@click.option('--docker-password', required=True)
@click.option('--debug', is_flag=True)
def main(hooks, hooks_group, hooks_prefix, hooks_client_id, hooks_access_token,
         docker_push, docker_registry, docker_repo, docker_username,
         docker_password, debug):
    """
    """

    if debug:
        logging.basicConfig(level=logging.DEBUG)


    taskcluster_hooks = taskcluster.Hooks(
        options=dict(
            credentials=dict(
                clientId=hooks_client_id,
                accessToken=hooks_access_token,
            )
        )
    )

    hooks_all = json.load(hooks)
    log.debug("Expected hooks:%s" % "\n - ".join([""] + list(hooks_all.keys())))

    click.echo("Gathering existing hooks for group `%s`. Might take some time ..." % hooks_group)
    hooks_existing = {
        hook['hookId']: hook
        for hook in taskcluster_hooks.listHooks(hooks_group).get('hooks', [])
        if hook.get('hookId', '').startswith(hooks_prefix)
    }

    log.debug("Existing hooks: %s" % "\n - ".join([""] + list(hooks_existing.keys())))  # noqa

    hooks_create, hooks_update, hooks_remove = diff_hooks(hooks_all,
                                                          hooks_existing,
                                                          hooks_prefix,
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
        hooks.createHook(hooks_group, hookId, hook)

    click.echo("Updating hooks:")

    for hookId, hook in hooks_update.items():
        click.echo(" - %s/%s" % (hooks_group, hookId))
        hooks.updateHook(hooks_group, hookId, hook)

    click.echo("Removing hooks:")

    for hookId, hook in hooks_remove.items():
        click.echo(" - %s/%s" % (hooks_group, hookId))
        hooks.removeHook(hooks_group, hookId)


if __name__ == "__main__":
    main()
