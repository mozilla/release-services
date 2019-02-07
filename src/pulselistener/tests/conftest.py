# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime
from datetime import timedelta

import pytest
from taskcluster.utils import stringDate


@pytest.fixture
def QueueMock():
    class Mock():
        def __init__(self):
            self.created_tasks = []

        def status(self, task_id):
            for status in ['failed', 'completed', 'exception', 'pending']:
                if status in task_id:
                    return {
                        'status': {
                            'state': status,
                        }
                    }
            assert False

        def task(self, task_id):
            now = datetime.utcnow()

            if 'retry:' in task_id:
                retry = int(task_id[task_id.index('retry:')+6])
            else:
                retry = 3

            return {
                'created': stringDate(now),
                'deadline': stringDate(now + timedelta(hours=2)),
                'dependencies': [],
                'expires': stringDate(now + timedelta(hours=24)),
                'payload': {
                    'command': ['/bin/command'],
                    'env': {},
                    'image': 'alpine',
                    'maxRunTime': 3600,
                },
                'priority': 'lowest',
                'provisionerId': 'aws-provisioner-v1',
                'requires': 'all-completed',
                'retries': retry,
                'scopes': [],
                'taskGroupId': 'group-{}'.format(task_id),
                'workerType': 'niceWorker'
            }

        def createTask(self, task_id, payload):
            self.created_tasks.append((task_id, payload))

    return Mock()


@pytest.fixture
def NotifyMock():
    class Mock():
        def __init__(self):
            self.email_obj = {}

        def email(self, obj):
            self.email_obj.update(obj)

    return Mock()


@pytest.fixture
def HooksMock():
    class Mock():
        def __init__(self):
            self.obj = {}

        def triggerHook(self, group_id, hook_id, payload):
            self.obj = {
              'group_id': group_id,
              'hook_id': hook_id,
              'payload': payload,
            }
            return {
                'status': {
                    'taskId': 'fake_task_id',
                },
            }

    return Mock()
