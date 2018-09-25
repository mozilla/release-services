# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.fixture(scope='session')
def QueueMock():
    class Mock():
        def status(self, task_id):
            for status in ['failed', 'completed', 'exception', 'pending']:
                if status in task_id:
                    return {
                        'status': {
                            'state': status,
                        }
                    }
            assert False

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
