# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest import mock


def test_taskcluster_index(mock_workflow):
    '''
    Test the Taskcluster indexation API
    '''
    mock_workflow.index_service = mock.Mock()
    mock_workflow.on_taskcluster = True
    mock_workflow.taskcluster_task_id = '12345deadbeef'
    mock_workflow.index('dummy.namespace', data={'test': 'dummy'})

    args = mock_workflow.index_service.insertTask.call_args[0]
    assert args[0] == 'project.releng.services.project.test.shipit_static_analysis.dummy.namespace'
    assert args[1]['taskId'] == '12345deadbeef'
    assert args[1]['data'] == {'test': 'dummy'}
