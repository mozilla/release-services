# -*- coding: utf-8 -*-
import asyncio
import os.path

import requests
from aiohttp import web

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

MODE_PHABRICATOR_POLLING = 'polling'
MODE_PHABRICATOR_WEBHOOK = 'webhook'


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

        # Choose a mode between polling and webhook
        self.mode = configuration.get('mode', MODE_PHABRICATOR_POLLING)
        assert self.mode in (MODE_PHABRICATOR_POLLING, MODE_PHABRICATOR_WEBHOOK)
        logger.info('Running in mode', mode=self.mode)

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

        # Add web route for new code review
        if self.mode == MODE_PHABRICATOR_WEBHOOK:
            self.routes.append(web.post('/codereview/new', self.new_code_review))

        # Load secure projects
        projects = self.api.search_projects(slugs=['secure-revision'])
        self.secure_projects = {
            p['phid']: p['fields']['name']
            for p in projects
        }
        logger.info('Loaded secure projects', projects=self.secure_projects.values())

        # Phabricator secure revision retries configuration
        self.phabricator_retries = configuration.get('phabricator_retries', 5)
        self.phabricator_sleep = configuration.get('phabricator_sleep', 10)
        assert isinstance(self.phabricator_retries, int)
        assert isinstance(self.phabricator_sleep, int)
        logger.info('Will retry Phabricator secure revision queries', retries=self.phabricator_retries, sleep=self.phabricator_sleep)  # noqa

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
        if self.mode != MODE_PHABRICATOR_POLLING:
            return

        while True:

            # Get new differential ids
            for diff in self.list_differential():
                try:
                    # Load revision to get repository
                    rev = self.api.load_revision(diff['revisionPHID'])

                    logger.info('Triggering task from polling', diff=diff['id'])
                    await self.trigger_task(diff, rev['fields']['repositoryPHID'])
                except Exception as e:
                    logger.error('Failed to trigger task from polling', error=str(e))

            # Sleep a bit before trying new diffs
            await asyncio.sleep(60)

    async def new_code_review(self, request):
        '''
        HTTP webhook used by HarborMaster on new diffs
        Mandatory query parameters:
        * diff as ID
        * repo as PHID
        * revision as ID
        '''
        diff_id = request.rel_url.query.get('diff')
        repo_phid = request.rel_url.query.get('repo')
        revision_id = request.rel_url.query.get('revision')

        if not diff_id or not repo_phid or not revision_id:
            logger.error('Invalid webhook parameters', path=request.path_qs)
            raise web.HTTPBadRequest(text='Invalid webhook parameters')

        # Check if the revision if public, and retry a few times
        # to give some time to the BMO daemon to update the revision
        public = False
        for step in range(self.phabricator_retries):
            if self.is_public_revision(int(revision_id)):
                public = True
                break
            else:
                sleep_time = self.phabricator_sleep * (1 + (step / self.phabricator_retries))
                logger.info('Sleeping until next retry', seconds=sleep_time)
                await asyncio.sleep(sleep_time)

        if not public:
            raise web.HTTPForbidden(text='Secure revision')

        # Lookup revision to check if it's public or secured
        # Load full diff from API
        diffs = self.api.search_diffs(diff_id=int(diff_id))
        if not diffs:
            logger.warn('Diff not found', diff_id=diff_id)
            raise web.HTTPNotFound(text='Diff not found')
        diff = diffs[0]

        try:
            logger.info('Triggering task from webhook', diff=diff_id, repo=repo_phid)
            created = await self.trigger_task(diff, repo_phid)
        except Exception as e:
            logger.error('Failed to trigger task from webhook', error=str(e))
            raise web.HTTPInternalServerError(text='Internal error: {}'.format(e))

        return web.Response(text=created and 'Task queued' or 'Skipped')

    def is_public_revision(self, revision_id):
        '''
        Check if a given revision is public (not in any secure projects)
        '''
        assert isinstance(revision_id, int)
        try:
            logger.info('Checking visibility status', revision_id=revision_id)
            rev = self.api.load_revision(rev_id=revision_id, attachments={'projects': True})
        except Exception as e:
            logger.info('Revision not accessible', revision_id=revision_id, error=e)
            return False

        if not rev:
            logger.warn('Revision not found', revision_id=revision_id)
            return False

        # Load projects and check againt secure projects
        projects = set(rev['attachments']['projects']['projectPHIDs'])
        if projects.intersection(self.secure_projects):
            logger.warn('Secure revision', revision_id=revision_id)
            return False

        logger.info('Revision is public', revision_id=revision_id)
        return True

    async def trigger_task(self, diff, repo_phid):
        '''
        Trigger a code review task using configured modes: Try or Taskcluster
        '''
        assert isinstance(diff, dict)
        assert 'phid' in diff and 'type' in diff
        assert diff['type'] == 'DIFF'

        # Skip unsupported repos
        if repo_phid not in self.repos:
            logger.info('Repository not enabled', repo=repo_phid)
            return False

        # Create new task
        if ACTION_TASKCLUSTER in self.actions:
            await self.create_task({
                'ANALYSIS_SOURCE': 'phabricator',
                'ANALYSIS_ID': diff['phid']
            })
        else:
            logger.info('Skipping Taskcluster task', diff=diff['phid'])

        # Put message in mercurial queue for try jobs
        # Do not wait so the webhook is not locked
        if ACTION_TRY in self.actions:
            assert self.mercurial_queue is not None, \
                'No mercurial queue to push on try!'
            self.mercurial_queue.put_nowait(diff)
        else:
            logger.info('Skipping Try job', diff=diff['phid'])

        return True


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
        self.http_port = int(os.environ.get('PORT', 9000))
        logger.info('HTTP webhook server will listen', port=self.http_port)

        task_monitoring.connect_taskcluster(
            self.taskcluster_client_id,
            self.taskcluster_access_token,
        )

        # Build mercurial worker & queue for mozilla unified
        if mercurial_conf.get('enabled', False):
            self.mercurial = MercurialWorker(
                self.phabricator_api,
                ssh_user=mercurial_conf['ssh_user'],
                ssh_key=mercurial_conf['ssh_key'],
                repo_url=REPO_UNIFIED,
                repo_dir=os.path.join(cache_root, 'sa-unified'),
                batch_size=mercurial_conf.get('batch_size', 100000),
            )
        else:
            self.mercurial = None
            logger.info('Mercurial worker is disabled')

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
        def _connect(hook):
            out = hook.connect_taskcluster(
                self.taskcluster_client_id,
                self.taskcluster_access_token,
            )
            if self.mercurial is not None:
                out &= hook.connect_mercurial_queue(self.mercurial.queue)
            return out
        consumers = [
            hook.build_consumer(self.pulse_user, self.pulse_password)
            for hook in hooks
            if _connect(hook)
        ]

        # Add monitoring process
        consumers.append(task_monitoring.run())

        # Add mercurial process
        if self.mercurial is not None:
            consumers.append(self.mercurial.run())

        # Hooks through web server
        consumers.append(self.build_webserver(hooks))

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

    def build_webserver(self, hooks):
        '''
        Build an async web server used by hooks
        '''
        app = web.Application()

        # Always add a simple test endpoint
        async def ping(request):
            return web.Response(text='pong')

        app.add_routes([web.get('/ping', ping)])

        # Add routes from hooks
        for hook in hooks:
            app.add_routes(hook.routes)

        # Finally build the webserver coroutine
        return web._run_app(app, port=self.http_port, print=logger.info)

    def add_revision(self, revision):
        '''
        Fetch a phabricator revision and push it in the mercurial queue
        '''
        if self.mercurial is None:
            logger.warn('Skip adding revision, mercurial worker is disabled', revision=revision)
            return

        rev = self.phabricator_api.load_revision(rev_id=revision)
        logger.info('Found revision', title=rev['fields']['title'])

        diffs = self.phabricator_api.search_diffs(diff_phid=rev['fields']['diffPHID'])
        assert len(diffs) == 1

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.mercurial.queue.put(diffs[0]))
        logger.info('Pushed revision in queue', rev=revision)
