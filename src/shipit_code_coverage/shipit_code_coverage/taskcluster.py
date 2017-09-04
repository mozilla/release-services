# -*- coding: utf-8 -*-
import os
import shutil
import requests

from shipit_code_coverage.utils import retry

index_base = 'https://index.taskcluster.net/v1/'
queue_base = 'https://queue.taskcluster.net/v1/'


def get_last_task():
    r = requests.get(index_base + 'task/gecko.v2.mozilla-central.latest.firefox.linux64-ccov-opt')
    last_task = r.json()
    return last_task['taskId']


def get_task(branch, revision):
    r = requests.get(index_base + 'task/gecko.v2.%s.revision.%s.firefox.linux64-ccov-opt' % (branch, revision))
    task = r.json()
    return task['taskId']


def get_task_details(task_id):
    r = requests.get(queue_base + 'task/' + task_id)
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


def download_artifact(task_id, suite, artifact):
    artifact_path = 'ccov-artifacts/' + task_id + '_' + suite + '_' + os.path.basename(artifact['name'])

    if os.path.exists(artifact_path):
        return artifact_path

    def perform_download():
        r = requests.get(queue_base + 'task/' + task_id + '/artifacts/' + artifact['name'], stream=True)

        with open(artifact_path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

    if not retry(perform_download):
        raise Exception('Failed downloading artifact in %s' % artifact_path)

    return artifact_path


def is_coverage_task(task):
    return task['task']['metadata']['name'].startswith('test-linux64-ccov')


def get_suite_name(task):
    name = task['task']['metadata']['name']
    name = name[len('test-linux64-ccov/opt-'):]
    return '-'.join([p for p in name.split('-') if p != 'e10s' and not p.isdigit()])
