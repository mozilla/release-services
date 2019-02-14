# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from cli_common.log import get_logger
from static_analysis_bot.lint import MozLintIssue
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

        # Find issues in dependencies
        issues = []
        for dep_id in task['dependencies']:
            try:
                dep_issues = self.load_analysis_task(dep_id, revision)
            except Exception as e:
                logger.warn('Failure during task analysis', task=task_id, error=e)
                continue

            if dep_issues is not None:
                issues += dep_issues

        if not issues:
            logger.info('No issues found, revision is OK', revision=revision)
            return

        # Publish using reporters
        for reporter in self.reporters.values():
            reporter.publish(issues, revision)

    def load_analysis_task(self, task_id, revision):
        '''
        Load artifacts and issues from an analysis task
        '''

        # Load base task
        task = self.queue_service.task(task_id)
        task_name = task['metadata'].get('name', 'unknown')
        logger.info('Lookup task dependency', id=task_id, name=task_name)

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

        # Load artifact logs from the last run
        run_id = status['status']['runs'][-1]['runId']
        artifacts = self.queue_service.listArtifacts(task_id, run_id)
        assert 'artifacts' in artifacts, 'Missing artifacts'
        logs = [
            artifact['name']
            for artifact in artifacts['artifacts']
            if artifact['storageType'] != 'reference' and artifact['contentType'].startswith('text/')
        ]

        # Read and parse issues from log files
        out = []
        for log in logs:
            try:
                out += self.read_log(task_id, task_name, run_id, log, revision)
            except Exception as e:
                logger.warn('Failed to read log', task_id=task_id, run_id=run_id, log=log, error=e)
        return out

    def read_log(self, task_id, task_name, run_id, artifact_name, revision):
        '''
        Read a log file from a dependant task
        '''
        logger.info('Reading log', task_id=task_id, log=artifact_name)

        # Load log from artifact API
        artifact = self.queue_service.getArtifact(task_id, run_id, artifact_name)
        assert 'response' in artifact, 'Failed loading artifact'

        # Lookup issues using marker
        issues = [
            line[line.index(ISSUE_MARKER) + len(ISSUE_MARKER):]
            for line in artifact['response'].content.decode('utf-8').split('\r\n')
            if ISSUE_MARKER in line
        ]
        if not issues:
            logger.warn('No issues found on failed task.', task_id=task_id, run_id=run_id)
            return

        # Convert to Issue instances
        logger.info('Found {} issues !'.format(len(issues)))
        return [
            self.build_issue(task_name, issue, revision)
            for issue in issues
        ]

    def build_issue(self, task_name, issue, revision):
        '''
        Convert a raw text issue into an Issue instance
        TODO: this should be simplified by using mach JSON output
        '''
        if task_name.startswith(MozLintIssue.TRY_PREFIX):
            return MozLintIssue.from_try(task_name, issue, revision)
        else:
            raise Exception('Unsupported task type', type=task_name)
