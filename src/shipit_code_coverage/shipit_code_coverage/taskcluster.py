# -*- coding: utf-8 -*-
import os
import shutil
from zipfile import BadZipFile
from zipfile import is_zipfile

import requests

from cli_common.utils import retry

index_base = 'https://index.taskcluster.net/v1/'
queue_base = 'https://queue.taskcluster.net/v1/'


class TaskclusterException(Exception):
    pass


def get_task(branch, revision, platform):
    if platform == 'linux':
        # A few days after https://bugzilla.mozilla.org/show_bug.cgi?id=1457393 is fixed,
        # we should only have 'linux64-ccov-debug' here and only support one platform_name
        # and no fallback.
        platform_names = ['linux64-ccov-debug', 'linux64-ccov-opt']
    elif platform == 'win':
        platform_names = ['win64-ccov-debug']
    else:
        raise TaskclusterException('Unsupported platform: %s' % platform)

    for i, platform_name in enumerate(platform_names):
        try:
            r = requests.get(index_base + 'task/gecko.v2.{}.revision.{}.firefox.{}'.format(branch, revision, platform_name))
            task = r.json()
            if r.status_code == requests.codes.ok:
                return task['taskId']
            else:
                if task['code'] == 'ResourceNotFound':
                    raise TaskclusterException('Code coverage build failed and was not indexed.')
                else:
                    raise TaskclusterException('Unknown TaskCluster index error.')
        except TaskclusterException:
            if i == len(platform_names) - 1:
                raise


def get_task_details(task_id):
    r = requests.get(queue_base + 'task/{}'.format(task_id))
    r.raise_for_status()
    return r.json()


def get_task_status(task_id):
    r = requests.get(queue_base + 'task/{}/status'.format(task_id))
    r.raise_for_status()
    return r.json()


def get_task_artifacts(task_id):
    r = requests.get(queue_base + 'task/{}/artifacts'.format(task_id))
    r.raise_for_status()
    return r.json()['artifacts']


def get_tasks_in_group(group_id):
    list_url = queue_base + 'task-group/{}/list'.format(group_id)

    r = requests.get(list_url, params={
        'limit': 200
    })
    r.raise_for_status()
    reply = r.json()
    tasks = reply['tasks']
    while 'continuationToken' in reply:
        r = requests.get(list_url, params={
            'limit': 200,
            'continuationToken': reply['continuationToken']
        })
        r.raise_for_status()
        reply = r.json()
        tasks += reply['tasks']
    return tasks


def download_artifact(artifact_path, task_id, artifact_name):
    if os.path.exists(artifact_path):
        return artifact_path

    def perform_download():
        r = requests.get(queue_base + 'task/{}/artifacts/{}'.format(task_id, artifact_name), stream=True)

        r.raise_for_status()

        with open(artifact_path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        if artifact_path.endswith('.zip') and not is_zipfile(artifact_path):
            raise BadZipFile('File is not a zip file')

    retry(perform_download)


TEST_PLATFORMS = ['test-linux64-ccov/debug', 'test-windows10-64-ccov/debug']


def is_coverage_task(task):
    return any(task['task']['metadata']['name'].startswith(t) for t in TEST_PLATFORMS)


def get_chunk(name):
    for t in TEST_PLATFORMS:
        if name.startswith(t):
            name = name[len(t) + 1:]
            break
    return '-'.join([p for p in name.split('-') if p != 'e10s'])


def get_suite(chunk_name):
    return '-'.join([p for p in chunk_name.split('-') if not p.isdigit()])


def get_platform(name):
    if 'linux' in name:
        return 'linux'
    elif 'windows' in name:
        return 'windows'
    else:
        raise Exception('Unknown platform')
