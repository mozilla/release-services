import os
import requests
import subprocess
import hglib

from cli_common.taskcluster import TaskclusterClient

from shipit_code_coverage import taskcluster
from shipit_code_coverage import coveralls


REPO_CENTRAL = 'https://hg.mozilla.org/mozilla-central'
REPO_DIR = 'mozilla-central'


def is_coverage_task(task):
    return task['task']['metadata']['name'].startswith('test-linux64-ccov')


def download_coverage_artifacts(build_task_id):
    try:
        os.mkdir('ccov-artifacts')
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
    url = 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s'
    r = requests.get(url % mercurial_commit)

    return r.text.split(' ')[0]


def generate_info(revision, coveralls_token):
    files = os.listdir('ccov-artifacts')
    ordered_files = []
    for fname in files:
        if not fname.endswith('.zip'):
            continue

        if 'gcno' in fname:
            ordered_files.insert(0, 'ccov-artifacts/' + fname)
        else:
            ordered_files.append('ccov-artifacts/' + fname)

    cmd = [
      'grcov',
      '-z',
      '-t', 'coveralls',
      '-s', REPO_DIR,
      '-p', '/home/worker/workspace/build/src/',
      '--commit-sha', get_github_commit(revision),
      '--token', coveralls_token,
    ]
    cmd.extend(ordered_files)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, err) = p.communicate()

    if p.returncode != 0:
        raise Exception('Error while running grcov:\n' + err.decode('utf-8'))

    return output


def clone_mozilla_central(revision):
    shared_dir = REPO_DIR + '-shared'
    cmd = hglib.util.cmdbuilder('robustcheckout',
                                REPO_CENTRAL,
                                REPO_DIR,
                                purge=True,
                                sharebase=shared_dir,
                                branch=b'tip')

    cmd.insert(0, hglib.HGPATH)
    proc = hglib.util.popen(cmd)
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError(cmd, proc.returncode, out, err)

    hg = hglib.open(REPO_DIR)

    hg.update(rev=revision, clean=True)


def go(secrets, client_id=None, client_token=None):
    tc_client = TaskclusterClient(client_id, client_token)

    secrets = tc_client.get_secrets(secrets, ['SHIPIT_CODE_COVERAGE_COVERALLS_TOKEN'])

    coveralls_token = secrets['SHIPIT_CODE_COVERAGE_COVERALLS_TOKEN']

    task_id = taskcluster.get_last_task()

    task_data = taskcluster.get_task_details(task_id)
    revision = task_data['payload']['env']['GECKO_HEAD_REV']

    download_coverage_artifacts(task_id)

    clone_mozilla_central(revision)

    output = generate_info(revision, coveralls_token)

    coveralls.upload(output)
