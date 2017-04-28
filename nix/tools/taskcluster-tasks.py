#!/usr/bin/env python3

import click
import click.exceptions
import copy
import json
import logging
import shlex
import subprocess
import taskcluster


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


def nix_to_tag(repo, image_path):
    if image_path.startswith('/nix/store'):
        tag = '-'.join(reversed(image_path[11:-7].split('-', 1)))
        return "%s:%s" % (repo, tag)
    return image_path

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
            if not cmp(tmp_hook, hook):
                update[hookId] = all[hookId]
        else:
            remove[hookId] = hook

    return create, update, remove


@click.group()
@click.option('--taskcluster-client-id', default=None, required=False)
@click.option('--taskcluster-access-token', default=None, required=False)
@click.option('--taskcluster-base-url', default=None, required=False)
@click.option('--docker-push', required=False, type=click.Path(resolve_path=True))
@click.option('--docker-registry', required=False, default="https://index.docker.com")  # noqa
@click.option('--docker-repo', required=False)
@click.option('--docker-username', required=False)
@click.option('--docker-password', required=False)
@click.option('--debug', is_flag=False)
@click.pass_context
def main(ctx, taskcluster_client_id, taskcluster_access_token,
         taskcluster_base_url, docker_push, docker_registry, docker_repo,
         docker_username, docker_password, debug):

    if debug:
        logging.basicConfig(level=logging.DEBUG)


    def get_taskcluster_tool(name):

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
                clientid=taskcluster_client_id,
                accesstoken=taskcluster_access_token,
            )

        if taskcluster_base_url:
            options = dict(
                baseurl=taskcluster_base_url,
            )


            name = name.lower()
            tool = getattr(
                taskcluster,
                name[0].upper(), name[1:],
            )

        if 'baseUrl' in options:
            return tool({
                **options,
                **{ "baseUrl": options['baseUrl'] + ("/%s/v1" % name) },
            })
        else:
            return tool(options)

    ctx.get_taskcluster_tool = get_taskcluster_tool


    def push_docker_image(image):

        # only upload if image is create via nix
        if image.startswith('/nix/store'):

            image_path = image
            image = nix_to_tag(docker_repo, image_path)
            tag = image[image.find(':', 1) + 1:]

            click.echo(' => ' + image)
            returncode, output = cmd(
                '%s %s %s -u "%s" -p "%s" -N "%s" -T "%s"' % (
                    docker_push,
                    image_path,
                    docker_registry,
                    docker_username,
                    docker_password,
                    docker_repo,
                    tag,
                ))

            if returncode != 0:
                click.echo(output)
                raise click.exceptions.ClickException("Error while pushing docker images")

        return image


    ctx.push_docker_image = push_docker_image




@main.command()
@click.pass_context
def tasks(ctx):
    print("YAAAAY")
    pass


@main.command()
@click.option('--hooks-file', required=True, type=click.File())
@click.option('--hooks-group', required=True)
@click.option('--hooks-prefix', required=True, default="services-")
@click.pass_context
def hooks(ctx, hooks_file, hooks_group, hooks_prefix):
    """ A tool for creating / updating taskcluster hooks (also creating and
        pushing docker images.
    """

    taskcluster_hooks = ctx.get_taskcluster_tool('hooks')

    hooks_all = json.load(hooks_file)
    click.echo("Expected hooks:%s" % "\n - ".join([""] + list(hooks_all.keys())))

    log.debug("Gathering existing hooks for group `%s`. Might take some time ..." % hooks_group)
    hooks_existing = {
        hook['hookId']: hook
        for hook in taskcluster_hooks.listHooks(hooks_group).get('hooks', [])
        if hook.get('hookId', '').startswith(hooks_prefix)
    }

    click.echo("Existing hooks: %s" % "\n - ".join([""] + list(hooks_existing.keys())))

    hooks_create, hooks_update, hooks_remove = \
        diff_hooks(hooks_all,
                   hooks_existing,
                   hooks_prefix,
                   docker_repo,
                   )

    log.debug("Hooks to create:%s" % "\n - ".join([""] + list(hooks_create.keys())))
    log.debug("Hooks to update:%s" % "\n - ".join([""] + list(hooks_update.keys())))
    log.debug("Hooks to remove:%s" % "\n - ".join([""] + list(hooks_remove.keys())))

    click.echo("(1) Pushing images to docker_registry:")

    for hookId, hook in hooks_create.items():
        hook_image = ctx.push_docker_image(hook['task']['payload']['image'])
        hooks_create[hookId]['task']['payload']['image'] = hook_image

    for hookId, hook in hooks_update.items():
        hook_image = ctx.push_docker_image(hook['task']['payload']['image'])
        hooks_update[hookId]['task']['payload']['image'] = hook_image

    click.echo("(2) Creating new hooks:")

    for hookId, hook in hooks_create.items():
        click.echo(" => %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.createHook(hooks_group, hookId, hook)

    click.echo("(3) Updating hooks:")

    for hookId, hook in hooks_update.items():
        click.echo(" => %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.updateHook(hooks_group, hookId, hook)

    click.echo("(4) Removing hooks:")

    for hookId, hook in hooks_remove.items():
        click.echo(" => %s/%s" % (hooks_group, hookId))
        taskcluster_hooks.removeHook(hooks_group, hookId)


if __name__ == "__main__":
    main()
