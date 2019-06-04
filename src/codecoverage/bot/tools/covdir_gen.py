# -*- coding: utf-8 -*-
import argparse
import os
from datetime import datetime

import requests
from taskcluster.utils import slugId

from cli_common import taskcluster
from code_coverage_bot.github import GitHubUtils
from code_coverage_bot.secrets import secrets

CODECOV_URL = 'https://codecov.io/api/gh/marco-c/gecko-dev/commit'
MC_REPO = 'https://hg.mozilla.org/mozilla-central'
HOOK_GROUP = 'project-releng'
HOOK_ID = 'services-{app_channel}-codecoverage/bot'

secrets.load(
    os.environ['TASKCLUSTER_SECRET'],
    os.environ['TASKCLUSTER_CLIENT_ID'],
    os.environ['TASKCLUSTER_ACCESS_TOKEN'],
)
github = GitHubUtils(
    '/tmp',
    os.environ['TASKCLUSTER_CLIENT_ID'],
    os.environ['TASKCLUSTER_ACCESS_TOKEN'],
)


def list_commits(maximum=None, unique_dates=False):
    '''
    List all the commits ingested on codecov
    '''
    params = {
        'access_token': secrets[secrets.CODECOV_ACCESS_TOKEN],
        'page': 1,
    }
    nb = 0
    days = set()
    while True:
        resp = requests.get(CODECOV_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if not data['commits']:
            return

        for commit in data['commits']:

            # Skip commit if that day has already been processed earlier
            day = datetime.strptime(commit['timestamp'], '%Y-%m-%d %H:%M:%S').date()
            if unique_dates and day in days:
                continue
            days.add(day)

            yield commit
            nb += 1

            if maximum is not None and nb >= maximum:
                return

        params['page'] += 1


def trigger_task(task_group_id, git_commit):
    '''
    Trigger a code coverage task to build covdir at a specified revision
    From a github revision (needs to be converted to mercurial!)
    '''
    name = 'covdir {} - {} - {}'.format(secrets[secrets.APP_CHANNEL], git_commit['commitid'], git_commit['timestamp'])
    print(name)

    # First convert to mercurial
    hg_revision = github.git_to_mercurial(git_commit['commitid'])

    # Then build task with mercurial revision
    hooks = taskcluster.get_service('hooks')
    payload = {
        'REPOSITORY': MC_REPO,
        'REVISION': hg_revision,
        'taskGroupId': task_group_id,
        'taskName': name,
    }
    hook_id = HOOK_ID.format(app_channel=secrets[secrets.APP_CHANNEL])
    return hooks.triggerHook(HOOK_GROUP, hook_id, payload)


def main():
    # CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument('--nb-tasks', type=int, default=5, help='NB of tasks to create')
    parser.add_argument('--unique-dates', action='store_true', default=False, help='Trigger only one task per day')
    args = parser.parse_args()

    # Generate a slug for task group
    task_group_id = slugId()
    print('Group', task_group_id)

    # Trigger a task for each commit
    for commit in list_commits(args.nb_tasks, args.unique_dates):
        out = trigger_task(task_group_id, commit)
        print('>>>', out['status']['taskId'])


if __name__ == '__main__':
    main()
