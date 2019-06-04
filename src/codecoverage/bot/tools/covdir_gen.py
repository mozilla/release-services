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
HOOK_ID = 'services-{app_channel}-codecoverage/bot-generation'

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


def list_commits(maximum=None, unique_dates=False, skip_commits=[]):
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

            # Convert git to mercurial revision
            commit['mercurial'] = github.git_to_mercurial(commit['commitid'])
            if commit['mercurial'] in skip_commits:
                print('Skipping already processed commit {}'.format(commit['mercurial']))
                continue

            yield commit
            nb += 1

            if maximum is not None and nb >= maximum:
                return

        params['page'] += 1


def trigger_task(task_group_id, commit, skip_commits=[]):
    '''
    Trigger a code coverage task to build covdir at a specified revision
    '''
    assert 'mercurial' in commit
    name = 'covdir {} - {} - {}'.format(secrets[secrets.APP_CHANNEL], commit['mercurial'], commit['timestamp'])
    hooks = taskcluster.get_service('hooks')
    payload = {
        'REPOSITORY': MC_REPO,
        'REVISION': commit['mercurial'],
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
    parser.add_argument('--group', type=str, default=slugId(), help='Task group to create/update')
    args = parser.parse_args()

    # List existing tags & commits
    print('Group', args.group)
    queue = taskcluster.get_service('queue')
    try:
        group = queue.listTaskGroup(args.group)
        commits = [
            task['task']['payload']['env']['REVISION']
            for task in group['tasks']
            if task['status']['state'] not in ('failed', 'exception')
        ]
        print('Found {} commits processed in task group {}'.format(len(commits), args.group))
    except Exception as e:
        print('Invalid task group : {}'.format(e))
        commits = []

    # Trigger a task for each commit
    for commit in list_commits(args.nb_tasks, args.unique_dates, commits):
        print('Triggering commit {mercurial} from {timestamp}'.format(**commit))
        out = trigger_task(args.group, commit)
        print('>>>', out['status']['taskId'])


if __name__ == '__main__':
    main()
