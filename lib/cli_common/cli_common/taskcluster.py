# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import copy
import datetime
import hashlib
import os
import re

import click
import requests
import taskcluster

from cli_common.log import get_logger

logger = get_logger(__name__)

TASKCLUSTER_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


with open(taskcluster._client_importer.__file__) as f:
    TASKCLUSTER_SERVICES = [
        line.split(' ')[1][1:]
        for line in f.read().split('\n')
        if line
    ]


def read_hosts():
    '''
    Read /etc/hosts to get hostnames
    on a Nix env (used for taskclusterProxy)
    Only reads ipv4 entries to avoid duplicates
    '''
    out = {}
    regex = re.compile(r'([\w:\-\.]+)')
    for line in open('/etc/hosts').readlines():
        if ':' in line:  # only ipv4
            continue
        x = regex.findall(line)
        if not x:
            continue
        ip, names = x[0], x[1:]
        out.update(dict(zip(names, [ip] * len(names))))

    return out


def get_options(client_id=None, access_token=None):
    '''
    Build Taskcluster credentials options
    '''

    if client_id is not None and access_token is not None:
        # Use provided credentials
        tc_options = {
            'credentials': {
                'clientId': client_id,
                'accessToken': access_token,
            },
            'rootUrl': 'https://taskcluster.net',
        }

    else:
        # Get taskcluster proxy host
        # as /etc/hosts is not used in the Nix image (?)
        hosts = read_hosts()
        if 'taskcluster' not in hosts:
            raise Exception('Missing taskcluster in /etc/hosts')

        # Load secrets from TC task context
        # with taskclusterProxy
        root_url = 'http://{}'.format(hosts['taskcluster'])
        logger.info('Taskcluster Proxy enabled', url=root_url)
        tc_options = {
            'rootUrl': root_url
        }

    tc_options['maxRetries'] = 12

    return tc_options


def get_service(service_name, client_id=None, access_token=None):
    '''
    Build a Taskcluster service instance from the environment
    Supports:
     * directly provided credentials
     * credentials from click
     * credentials from environment variables
     * taskclusterProxy
    '''
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
    options = get_options(client_id, access_token)
    return getattr(taskcluster, service_name.capitalize())(options)


def get_secrets(name,
                project_name,
                required=[],
                existing=dict(),
                taskcluster_client_id=None,
                taskcluster_access_token=None,
                ):
    '''
    Fetch a specific set of secrets by name and verify that the required
    secrets exist.

    Merge secrets in the following order (the latter overrides the former):
        - `existing` argument
        - common secrets, specified under the `common` key in the secrets
          object
        - project specific secrets, specified under the `project_name` key in
          the secrets object
    '''

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
    '''
    Load an artifact from the last execution of an hook
    '''

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


def create_blob_artifact(queue_service, task_id, run_id, path, content, content_type, ttl):
    '''
    Manually create and upload a blob artifact to use a specific content type
    '''
    assert isinstance(content, str)
    assert isinstance(ttl, datetime.timedelta)

    # Create artifact on Taskcluster
    sha256 = hashlib.sha256(content.encode('utf-8')).hexdigest()
    resp = queue_service.createArtifact(
        task_id,
        run_id,
        path,
        {
            'storageType': 'blob',
            'expires': (datetime.datetime.utcnow() + ttl).strftime(TASKCLUSTER_DATE_FORMAT),
            'contentType': content_type,
            'contentSha256': sha256,
            'contentLength': len(content),
        }
    )
    assert resp['storageType'] == 'blob', 'Not a blob storage'
    assert len(resp['requests']) == 1, 'Should only get one request'
    request = resp['requests'][0]
    assert request['method'] == 'PUT', 'Should get a PUT request'

    # Push the artifact on storage service
    push = requests.put(
        url=request['url'],
        headers=request['headers'],
        data=content,
    )
    push.raise_for_status()

    # Build the absolute url
    return f'https://queue.taskcluster.net/v1/task/{task_id}/runs/{run_id}/artifacts/{path}'
