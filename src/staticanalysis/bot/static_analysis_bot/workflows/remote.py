# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

from static_analysis_bot.workflows.base import Workflow


class RemoteWorkflow(Workflow):
    '''
    Secondary workflow to analyze the output from a try task group
    '''
    def run(self, revision, task_id):

        # Task id is provided (dev) or from env (task)
        if task_id is None:
            task_id = os.environ.get('TASK_ID')

        assert task_id is not None, 'Missing Taskcluster task id'
