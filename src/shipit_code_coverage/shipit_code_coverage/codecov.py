import os
import requests
import subprocess

from shipit_code_coverage import taskcluster
from shipit_code_coverage import coveralls


def is_coverage_task(task):
    return task['task']['metadata']['name'].startswith('test-linux64-ccov')


def download_coverage_artifacts(build_task_id):
    try:
        os.mkdir("ccov-artifacts")
    except:
        pass

    task_data = taskcluster.get_task_details(build_task_id)

    artifacts = taskcluster.get_task_artifacts(build_task_id)
    for artifact in artifacts:
        if 'target.code-coverage-gcno.zip' in artifact['name']:
            taskcluster.download_artifact(build_task_id, artifact)

    tasks = taskcluster.get_tasks_in_group(task_data['taskGroupId'])
    test_tasks = [t for t in tasks if is_coverage_task(t)]
    for test_task in test_tasks:
        test_task_id = test_task['status']['taskId']
        artifacts = taskcluster.get_task_artifacts(test_task_id)
        for artifact in artifacts:
            if 'code-coverage-gcda.zip' in artifact['name']:
                taskcluster.download_artifact(test_task_id, artifact)


def get_github_commit(mercurial_commit):
    url = "https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s"
    r = requests.get(url % mercurial_commit)

    return r.text.split(" ")[0]


def generate_info(revision):
    files = os.listdir("ccov-artifacts")
    ordered_files = []
    for fname in files:
        if not fname.endswith('.zip'):
            continue

        if 'gcno' in fname:
            ordered_files.insert(0, "ccov-artifacts/" + fname)
        else:
            ordered_files.append("ccov-artifacts/" + fname)

    cmd = [
      'grcov',
      '-z',
      '-t', 'coveralls',
      '-s', '/home/worker/workspace/build/src/',
      '--commit-sha', get_github_commit(revision),
      '--token', '95dgNaxbGORBDEaxioPGWXT0FskF8eDzd'
    ]
    cmd.extend(ordered_files[:3])

    proc = subprocess.Popen(cmd, stdout=open("output.json", 'w'))

    ret = proc.wait()
    if ret != 0:
        raise Exception("Error while running grcov:" + str(ret))


def go():
    task_id = taskcluster.get_last_task()

    task_data = taskcluster.get_task_details(task_id)
    revision = task_data["payload"]["env"]["GECKO_HEAD_REV"]

    # download_coverage_artifacts(task_id)

    generate_info(revision)

    coveralls.upload()
