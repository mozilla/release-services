# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import requests

from cli_common.log import get_logger
from static_analysis_bot.workflows.base import Workflow

logger = get_logger(__name__)


ISSUE_MARKER = 'TEST-UNEXPECTED-ERROR | '


class RemoteWorkflow(Workflow):
    '''
    Secondary workflow to analyze the output from a try task group
    '''
    def run(self, revision, task_id):

        # Task id is provided (dev) or from env (task)
        if task_id is None:
            task_id = os.environ.get('TASK_ID')

        assert task_id is not None, 'Missing Taskcluster task id'

        # Load task description
        task = self.queue_service.task(task_id)
        assert len(task['dependencies']) > 0, 'No task dependencies to analyze'

        # Lookup dependencies
        for dep_id in task['dependencies']:
            self.load_analysis_task(dep_id)

    def load_analysis_task(self, task_id):
        '''
        Load artifacts and issues from an analysis task
        '''

        # Load base task
        task = self.queue_service.task(task_id)
        logger.info('Lookup task dependency', id=task_id, name=task['metadata'].get('name', 'unknown'))

        # Load task status
        status = self.queue_service.status(task_id)
        assert 'status' in status, 'No status data for {}'.format(task_id)
        state = status['status']['state']

        # Process only the failed tasks
        # A completed task here means the analyzer did not find any issues
        if state == 'completed':
            logger.info('No issues detected by completed task', id=task_id)
            return
        elif state != 'failed':
            logger.warn('Unsupported task state', state=state, id=task_id)
            return

        # Load artifact log from the last run
        run_id = status['status']['runs'][-1]['runId']
        artifact_url = self.queue_service.buildUrl('getArtifact', task_id, run_id, 'public/logs/live.log')
        resp = requests.get(artifact_url, allow_redirects=True)
        resp.raise_for_status()

        # Lookup issues using marker
        issues = [
            line[line.index(ISSUE_MARKER) + len(ISSUE_MARKER):]
            for line in resp.content.decode('utf-8').split('\r\n')
            if ISSUE_MARKER in line
        ]
        if not issues:
            logger.warn('No issues found on failed task.', task_id=task_id, run_id=run_id)
            return

        # Debug
        logger.info('Found {} issues !'.format(len(issues)))
        for issue in issues:
            logger.info(issue)
