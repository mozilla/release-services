import os
import shutil
import subprocess
import time
import argparse
import requests


def get_last_task():
    r = requests.get('https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.latest.firefox.linux64-ccov-opt')
    last_task = r.json()
    return last_task['taskId']


def get_task(branch, revision):
    r = requests.get('https://index.taskcluster.net/v1/task/gecko.v2.%s.revision.%s.firefox.linux64-ccov-opt' % (branch, revision))
    task = r.json()
    return task['taskId']


def get_task_details(task_id):
    r = requests.get('https://queue.taskcluster.net/v1/task/' + task_id)
    return r.json()


def get_task_artifacts(task_id):
    r = requests.get('https://queue.taskcluster.net/v1/task/' + task_id + '/artifacts')
    return r.json()['artifacts']


def get_tasks_in_group(group_id):
    r = requests.get('https://queue.taskcluster.net/v1/task-group/' + group_id + '/list', params={
        'limit': 200
    })
    reply = r.json()
    tasks = reply['tasks']
    while 'continuationToken' in reply:
        r = requests.get('https://queue.taskcluster.net/v1/task-group/' + group_id + '/list', params={
            'limit': 200,
            'continuationToken': reply['continuationToken']
        })
        reply = r.json()
        tasks += reply['tasks']
    return tasks


def download_artifact(task_id, artifact):
    r = requests.get('https://queue.taskcluster.net/v1/task/' + task_id + '/artifacts/' + artifact['name'], stream=True)
    with open(os.path.join('ccov-artifacts', task_id + '_' + os.path.basename(artifact['name'])), 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
