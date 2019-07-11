# -*- coding: utf-8 -*-
import os
import shutil
from zipfile import BadZipFile
from zipfile import is_zipfile

import requests

from code_coverage_bot.utils import retry
from code_coverage_tools.taskcluster import TaskclusterConfig

taskcluster_config = TaskclusterConfig()

index_base = 'https://index.taskcluster.net/v1/'
queue_base = 'https://queue.taskcluster.net/v1/'


class TaskclusterException(Exception):
    pass


def get_task(branch, revision, platform):
    if platform == 'linux':
        platform_name = 'linux64-ccov-debug'
        product = 'firefox'
    elif platform == 'windows':
        platform_name = 'win64-ccov-debug'
        product = 'firefox'
    elif platform == 'android-test':
        platform_name = 'android-test-ccov'
        product = 'mobile'
    elif platform == 'android-emulator':
        platform_name = 'android-api-16-ccov-debug'
        product = 'mobile'
    else:
        raise TaskclusterException('Unsupported platform: %s' % platform)

    r = requests.get(index_base + 'task/gecko.v2.{}.revision.{}.{}.{}'.format(branch, revision, product, platform_name))
    task = r.json()
    if r.status_code == requests.codes.ok:
        return task['taskId']
    else:
        if task['code'] == 'ResourceNotFound':
            return None
        else:
            raise TaskclusterException('Unknown TaskCluster index error.')


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


BUILD_PLATFORMS = [
    'build-linux64-ccov/debug',
    'build-win64-ccov/debug',
    'build-android-test-ccov/opt',
]


TEST_PLATFORMS = [
    'test-linux64-ccov/debug',
    'test-windows10-64-ccov/debug',
    'test-android-em-4.3-arm7-api-16-ccov/debug',
] + BUILD_PLATFORMS


def is_coverage_task(task):
    return any(task['task']['metadata']['name'].startswith(t) for t in TEST_PLATFORMS)


def get_chunk(name):
    # Some tests are run on build machines, we define a placeholder chunk for those.
    if name in BUILD_PLATFORMS:
        return 'build'

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
    elif 'win' in name:
        return 'windows'
    elif 'android-test' in name:
        return 'android-test'
    elif 'android-em' in name:
        return 'android-emulator'
    else:
        raise Exception('Unknown platform')
