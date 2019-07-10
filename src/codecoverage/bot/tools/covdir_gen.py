# -*- coding: utf-8 -*-
import argparse
import os
from datetime import datetime

import requests
from code_coverage_tools.taskcluter import TaskclusterConfig
from taskcluster.utils import slugId

from code_coverage_bot.github import GitHubUtils
from code_coverage_bot.secrets import secrets

CODECOV_URL = 'https://codecov.io/api/gh/marco-c/gecko-dev/commit'
MC_REPO = 'https://hg.mozilla.org/mozilla-central'
HOOK_GROUP = 'project-releng'
HOOK_ID = 'services-{app_channel}-codecoverage/bot-generation'

taskcluster = TaskclusterConfig()
taskcluster.auth(
    os.environ['TASKCLUSTER_CLIENT_ID'],
    os.environ['TASKCLUSTER_ACCESS_TOKEN'],
)
secrets.load(
    os.environ['TASKCLUSTER_SECRET'],
)
github = GitHubUtils(
    '/tmp',
    os.environ['TASKCLUSTER_CLIENT_ID'],
    os.environ['TASKCLUSTER_ACCESS_TOKEN'],
)


def list_commits(maximum=None, unique=None, skip_commits=[]):
    '''
    List all the commits ingested on codecov
    '''
    assert unique in (None, 'week', 'day')
    params = {
        'access_token': secrets[secrets.CODECOV_ACCESS_TOKEN],
        'page': 1,
    }
    nb = 0
    dates = set()
    while True:
        resp = requests.get(CODECOV_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if not data['commits']:
            return

        for commit in data['commits']:

            # Skip commit if that day or week has already been processed earlier
            day = datetime.strptime(commit['timestamp'], '%Y-%m-%d %H:%M:%S').date()
            week = day.isocalendar()[:2]
            if unique == 'day' and day in dates:
                continue
            if unique == 'week' and week in dates:
                continue
            dates.add(day)
            dates.add(week)

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


def trigger_task(task_group_id, commit):
    '''
    Trigger a code coverage task to build covdir at a specified revision
    '''
    assert 'mercurial' in commit
    name = 'covdir {} - {} - {}'.format(secrets[secrets.APP_CHANNEL], commit['timestamp'], commit['mercurial'])
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
    parser.add_argument('--unique', choices=('day', 'week'), help='Trigger only one task per day or week')
    parser.add_argument('--group', type=str, default=slugId(), help='Task group to create/update')
    parser.add_argument('--dry-run', action='store_true', default=False, help='List actions without triggering any new task')
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
    for commit in list_commits(args.nb_tasks, args.unique, commits):
        print('Triggering commit {mercurial} from {timestamp}'.format(**commit))
        if args.dry_run:
            print('>>> No trigger on dry run')
        else:
            out = trigger_task(args.group, commit)
            print('>>>', out['status']['taskId'])


if __name__ == '__main__':
    main()
