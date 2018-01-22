# -*- coding: utf-8 -*-
import os
import shutil
import requests

from shipit_code_coverage.utils import retry

index_base = 'https://index.taskcluster.net/v1/'
queue_base = 'https://queue.taskcluster.net/v1/'


def _get_build_platform_name(platform):
    if platform == 'linux':
        return 'linux64-ccov-opt'
    elif platform == 'win':
        return 'win64-ccov-debug'
    else:
        raise Exception('Unsupported platform: %s' % platform)


def get_last_task(platform):
    r = requests.get(index_base + 'task/gecko.v2.mozilla-central.latest.firefox.' + _get_build_platform_name(platform))
    last_task = r.json()
    return last_task['taskId']


def get_task(branch, revision, platform):
    r = requests.get(index_base + 'task/gecko.v2.%s.revision.%s.firefox.%s' % (branch, revision, _get_build_platform_name(platform)))
    task = r.json()
    if r.status_code == requests.codes.ok:
        return task['taskId']
    else:
        if task['code'] == 'ResourceNotFound':
            raise Exception('Code coverage build failed and was not indexed.')
        else:
            raise Exception('Unknown TaskCluster index error.')


def get_task_details(task_id):
    r = requests.get(queue_base + 'task/' + task_id)
    return r.json()


def get_task_status(task_id):
    r = requests.get(queue_base + 'task/' + task_id + '/status')
    return r.json()


def get_task_artifacts(task_id):
    r = requests.get(queue_base + 'task/' + task_id + '/artifacts')
    return r.json()['artifacts']


def get_tasks_in_group(group_id):
    list_url = queue_base + 'task-group/' + group_id + '/list'

    r = requests.get(list_url, params={
        'limit': 200
    })
    reply = r.json()
    tasks = reply['tasks']
    while 'continuationToken' in reply:
        r = requests.get(list_url, params={
            'limit': 200,
            'continuationToken': reply['continuationToken']
        })
        reply = r.json()
        tasks += reply['tasks']
    return tasks


def download_artifact(task_id, chunk, platform, artifact):
    artifact_path = 'ccov-artifacts/%s_%s_%s' % (platform, chunk, os.path.basename(artifact['name']))

    if os.path.exists(artifact_path):
        return artifact_path

    def perform_download():
        r = requests.get(queue_base + 'task/%s/artifacts/%s' % (task_id, artifact['name']), stream=True)

        with open(artifact_path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    if not retry(perform_download):
        raise Exception('Failed downloading artifact in %s' % artifact_path)

    return artifact_path


TEST_PLATFORMS = ['test-linux64-ccov/opt', 'test-windows10-64-ccov/debug']


def is_coverage_task(task):
    return any(task['task']['metadata']['name'].startswith(t) for t in TEST_PLATFORMS)


def get_chunk_name(task):
    name = task['task']['metadata']['name']
    for t in TEST_PLATFORMS:
        if name.startswith(t):
            name = name[len(t) + 1:]
            break
    return '-'.join([p for p in name.split('-') if p != 'e10s'])


def get_suite_name(chunk_name):
    return '-'.join([p for p in chunk_name.split('-') if not p.isdigit()])


def get_platform_name(task):
    name = task['task']['metadata']['name']
    if 'linux' in name:
        return 'linux'
    elif 'windows' in name:
        return 'windows'
    else:
        raise Exception('Unknown platform')
