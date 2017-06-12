# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import copy
import os
import re
import taskcluster

from cli_common.log import get_logger


logger = get_logger(__name__)


with open(taskcluster._client_importer.__file__) as f:
    TASKCLUSTER_SERVICES = [
        line.split(' ')[1][1:]
        for line in f.read().split('\n')
        if line
    ]


def read_hosts():
    """
    Read /etc/hosts to get hostnames
    on a Nix env (used for taskclusterProxy)
    Only reads ipv4 entries to avoid duplicates
    """
    out = {}
    regex = re.compile('([\w:\-\.]+)')
    for line in open('/etc/hosts').readlines():
        if ':' in line:  # only ipv4
            continue
        x = regex.findall(line)
        if not x:
            continue
        ip, names = x[0], x[1:]
        out.update(dict(zip(names, [ip] * len(names))))

    return out


def get_options(service_endpoint, client_id=None, access_token=None):
    """
    Build Taskcluster credentials options
    """

    if client_id is not None and access_token is not None:
        # Use provided credentials
        tc_options = {
            'credentials': {
                'clientId': client_id,
                'accessToken': access_token,
            }
        }

    else:
        # Get taskcluster proxy host
        # as /etc/hosts is not used in the Nix image (?)
        hosts = read_hosts()
        if 'taskcluster' not in hosts:
            raise Exception('Missing taskcluster in /etc/hosts')

        # Load secrets from TC task context
        # with taskclusterProxy
        base_url = 'http://{}/{}'.format(
            hosts['taskcluster'],
            service_endpoint
        )
        logger.info('Taskcluster Proxy enabled', url=base_url)
        tc_options = {
            'baseUrl': base_url
        }

    return tc_options


def get_service(service_name, client_id=None, access_token=None):
    """
    Build a Taskcluster service instance from the environment
    Supports:
     * directly provided credentials
     * credentials from click
     * credentials from environment variables
     * taskclusterProxy
    """
    if service_name not in TASKCLUSTER_SERVICES:
        raise Exception('Service `{}` does not exists.'.format(service_name))

    # Credentials preference: Use click variables
    if client_id is None and access_token is None:
        try:
            ctx = click.get_current_context()
            client_id = ctx.params.get('taskcluster_client_id')
            access_token = ctx.params.get('taskcluster_access_token')
        except RuntimeError:
            pass  # no active context

    # Credentials preference: Use env. variables
    if client_id is None and access_token is None:
        client_id = os.environ.get('TASKCLUSTER_CLIENT_ID')
        access_token = os.environ.get('TASKCLUSTER_ACCESS_TOKEN')

    # Instanciate service
    options = get_options(service_name + '/v1', client_id, access_token)
    return getattr(taskcluster, service_name.capitalize())(options)


def get_secrets(name,
                project_name,
                required=[],
                existing=dict(),
                taskcluster_client_id=None,
                taskcluster_access_token=None,
                ):
    """
    Fetch a specific set of secrets by name
    - merge project specific secrets
    - check that all required secrets are present
    - extend existing set of secrets
    """

    secrets = dict()
    if existing:
        secrets = copy.deepcopy(existing)

    all_secrets = dict()
    if name:
        secrets_service = get_service('secrets',
                                      taskcluster_client_id,
                                      taskcluster_access_token,
                                      )
        all_secrets = secrets_service.get(name).get('secret', dict())

    secrets_common = all_secrets.get('common', dict())
    secrets.update(secrets_common)

    secrets_app = all_secrets.get(project_name, dict())
    secrets.update(secrets_app)

    for required_secret in required:
        if required_secret not in secrets:
            raise Exception('Missing value {} in secrets.'.format(required_secret))

    return secrets


def get_hook_artifact(hook_group_id, hook_id, artifact_name, client_id=None,
                      access_token=None):
    """
    Load an artifact from the last execution of an hook
    """

    # Get last run from hook
    hooks = get_service('hooks', client_id, access_token)
    hook_status = hooks.getHookStatus(hook_group_id, hook_id)
    last_fire = hook_status.get('lastFire')
    if last_fire is None:
        raise Exception('Hook did not fire')
    task_id = last_fire['taskId']

    # Get successful run for this task
    queue = get_service('queue', client_id, access_token)
    task_status = queue.status(task_id)
    if task_status['status']['state'] != 'completed':
        raise Exception('Task {} is not completed'.format(task_id))
    run_id = None
    for run in task_status['status']['runs']:
        if run['state'] == 'completed':
            run_id = run['runId']
            break
    if run_id is None:
        raise Exception('No completed run found')

    # Load artifact from task run
    return queue.getArtifact(task_id, run_id, artifact_name)
