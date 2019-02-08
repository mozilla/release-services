# -*- coding: utf-8 -*-
import asyncio
import os.path

import requests

from cli_common.log import get_logger
from cli_common.pulse import run_consumer
from cli_common.utils import retry
from pulselistener import task_monitoring
from pulselistener.config import REPO_UNIFIED
from pulselistener.hook import Hook
from pulselistener.hook import PulseHook
from pulselistener.mercurial import MercurialWorker

logger = get_logger(__name__)

ACTION_TASKCLUSTER = 'taskcluster'
ACTION_TRY = 'try'


class HookPhabricator(Hook):
    '''
    Taskcluster hook handling the static analysis
    for Phabricator differentials
    '''
    latest_id = None

    def __init__(self, configuration):
        assert 'hookId' in configuration
        super().__init__(
            'project-releng',
            configuration['hookId'],
        )

        # Connect to Phabricator API
        assert 'phabricator_api' in configuration
        self.api = configuration['phabricator_api']

        # List enabled repositories
        enabled = configuration.get('repositories', ['mozilla-central', ])
        self.repos = {
            r['phid']: r
            for r in self.api.list_repositories()
            if r['fields']['name'] in enabled
        }
        assert len(self.repos) > 0, 'No repositories enabled'
        logger.info('Enabled Phabricator repositories', repos=[r['fields']['name'] for r in self.repos.values()])

        # Get actions to do on new diff
        self.actions = configuration.get('actions', [ACTION_TASKCLUSTER, ])
        logger.info('Enabled actions', actions=self.actions)

        # Start by getting top id
        diffs = self.api.search_diffs(limit=1)
        assert len(diffs) == 1
        self.latest_id = diffs[0]['id']

    def list_differential(self):
        '''
        List new differential items using pagination
        using an iterator
        '''
        cursor = self.latest_id
        while cursor is not None:
            diffs, cursor = self.api.search_diffs(
                order='oldest',
                limit=20,
                after=self.latest_id,
                output_cursor=True,
            )
            if not diffs:
                break

            for diff in diffs:
                yield diff

            # Update the latest id
            if cursor and cursor['after']:
                self.latest_id = cursor['after']
            elif len(diffs) > 0:
                self.latest_id = diffs[-1]['id']

    async def build_consumer(self, *args, **kwargs):
        '''
        Query phabricator differentials regularly
        '''
        while True:

            # Get new differential ids
            for diff in self.list_differential():
                if diff['type'] != 'DIFF':
                    logger.info('Skipping differential, not a diff', id=diff['id'], type=diff['type'])
                    continue

                # Load revision to check the repository is authorized
                rev = self.api.load_revision(diff['revisionPHID'])
                repo_phid = rev['fields']['repositoryPHID']
                if repo_phid not in self.repos:
                    logger.info('Skipping differential, repo not enabled', id=diff['id'], repo=repo_phid)
                    continue

                # Create new task
                if ACTION_TASKCLUSTER in self.actions:
                    await self.create_task({
                        'ANALYSIS_SOURCE': 'phabricator',
                        'ANALYSIS_ID': diff['phid']
                    })
                else:
                    logger.info('Skipping Taskcluster task', diff=diff['phid'])

                # Put message in mercurial queue for try jobs
                if ACTION_TRY in self.actions:
                    await self.mercurial_queue.put(diff)
                else:
                    logger.info('Skipping Try job', diff=diff['phid'])

            # Sleep a bit before trying new diffs
            await asyncio.sleep(60)


class HookCodeCoverage(PulseHook):
    '''
    Taskcluster hook handling the code coverage
    '''
    def __init__(self, configuration):
        assert 'hookId' in configuration
        self.triggered_groups = set()
        super().__init__(
            'project-releng',
            configuration['hookId'],
            'exchange/taskcluster-queue/v1/task-group-resolved',
            '#'
        )

    def is_coverage_task(self, task):
        return any(task['task']['metadata']['name'].startswith(s) for s in ['build-linux64-ccov', 'build-win64-ccov'])

    def get_build_task_in_group(self, group_id):
        if group_id in self.triggered_groups:
            logger.info('Received duplicated groupResolved notification', group=group_id)
            return None

        def maybe_trigger(tasks):
            for task in tasks:
                if self.is_coverage_task(task):
                    self.triggered_groups.add(group_id)
                    return task

            return None

        list_url = 'https://queue.taskcluster.net/v1/task-group/{}/list'.format(group_id)

        def retrieve_coverage_task():
            r = requests.get(list_url, params={
                'limit': 200
            })
            r.raise_for_status()
            reply = r.json()
            task = maybe_trigger(reply['tasks'])

            while task is None and 'continuationToken' in reply:
                r = requests.get(list_url, params={
                    'limit': 200,
                    'continuationToken': reply['continuationToken']
                })
                r.raise_for_status()
                reply = r.json()
                task = maybe_trigger(reply['tasks'])

            return task

        try:
            return retry(retrieve_coverage_task)
        except requests.exceptions.HTTPError:
            return None

    def parse(self, body):
        '''
        Extract revisions from payload
        '''
        taskGroupId = body['taskGroupId']

        build_task = self.get_build_task_in_group(taskGroupId)
        if build_task is None:
            return None

        repository = build_task['task']['payload']['env']['GECKO_HEAD_REPOSITORY']

        if repository not in ['https://hg.mozilla.org/mozilla-central', 'https://hg.mozilla.org/try']:
            logger.warn('Received groupResolved notification for a coverage task in an unexpected branch', repository=repository)
            return None

        logger.info('Received groupResolved notification for coverage builds', repository=repository, revision=build_task['task']['payload']['env']['GECKO_HEAD_REV'], group=taskGroupId)  # noqa

        return [{
            'REPOSITORY': repository,
            'REVISION': build_task['task']['payload']['env']['GECKO_HEAD_REV'],
        }]


class PulseListener(object):
    '''
    Listen to pulse messages and trigger new tasks
    '''
    def __init__(self,
                 pulse_user,
                 pulse_password,
                 hooks_configuration,
                 mercurial_conf,
                 phabricator_api,
                 cache_root,
                 taskcluster_client_id=None,
                 taskcluster_access_token=None,
                 ):

        self.pulse_user = pulse_user
        self.pulse_password = pulse_password
        self.hooks_configuration = hooks_configuration
        self.taskcluster_client_id = taskcluster_client_id
        self.taskcluster_access_token = taskcluster_access_token
        self.phabricator_api = phabricator_api

        task_monitoring.connect_taskcluster(
            self.taskcluster_client_id,
            self.taskcluster_access_token,
        )

        # Build mercurial worker & queue for mozilla unified
        self.mercurial = MercurialWorker(
            self.phabricator_api,
            ssh_user=mercurial_conf['ssh_user'],
            ssh_key=mercurial_conf['ssh_key'],
            repo_url=REPO_UNIFIED,
            repo_dir=os.path.join(cache_root, 'sa-unified'),
        )

    def run(self):

        # Build hooks for each conf
        hooks = [
            self.build_hook(conf)
            for conf in self.hooks_configuration
        ]
        if not hooks:
            raise Exception('No hooks created')

        # Run hooks pulse listeners together
        # but only use hooks with active definitions
        consumers = [
            hook.build_consumer(self.pulse_user, self.pulse_password)
            for hook in hooks
            if hook.connect_taskcluster(
                self.taskcluster_client_id,
                self.taskcluster_access_token,
            ) and hook.connect_mercurial_queue(self.mercurial.queue)
        ]

        # Add monitoring process
        consumers.append(task_monitoring.run())

        # Add mercurial process
        consumers.append(self.mercurial.run())

        # Run all consumers together
        run_consumer(asyncio.gather(*consumers))

    def build_hook(self, conf):
        '''
        Build a new hook instance according to configuration
        '''
        assert isinstance(conf, dict)
        assert 'type' in conf
        conf['phabricator_api'] = self.phabricator_api
        classes = {
            'static-analysis-phabricator': HookPhabricator,
            'code-coverage': HookCodeCoverage,
        }
        hook_class = classes.get(conf['type'])
        if hook_class is None:
            raise Exception('Unsupported hook {}'.format(conf['type']))

        return hook_class(conf)

    def add_revision(self, revision):
        '''
        Fetch a phabricator revision and push it in the mercurial queue
        '''
        rev = self.phabricator_api.load_revision(rev_id=revision)
        logger.info('Found revision', title=rev['fields']['title'])

        diffs = self.phabricator_api.search_diffs(diff_phid=rev['fields']['diffPHID'])
        assert len(diffs) == 1

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.mercurial.queue.put(diffs[0]))
        logger.info('Pushed revision in queue', rev=revision)
