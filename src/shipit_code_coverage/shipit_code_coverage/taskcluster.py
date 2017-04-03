import os
import shutil
import requests

index_base = 'https://index.taskcluster.net/v1/'
queue_base = 'https://queue.taskcluster.net/v1/'


def get_last_task():
    r = requests.get(index_base + 'task/gecko.v2.mozilla-central.latest.firefox.linux64-ccov-opt')  # NOQA
    last_task = r.json()
    return last_task['taskId']


def get_task(branch, revision):
    r = requests.get(index_base + 'task/gecko.v2.%s.revision.%s.firefox.linux64-ccov-opt' % (branch, revision))  # NOQA
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


def download_artifact(task_id, artifact):
    r = requests.get(queue_base + 'task/' + task_id + '/artifacts/' + artifact['name'], stream=True)  # NOQA

    artifact_path = 'ccov-artifacts/' + task_id + '_' + os.path.basename(artifact['name'])  # NOQA
    with open(artifact_path, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
