# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch
import os
import json

from shipit_taskcluster.taskcluster_utils import get_queue_group_state


def mocked_listtaskgroup(task_group_id):
    filename = os.path.join(os.path.dirname(__file__), 'testdata', task_group_id)
    with open(filename, 'r') as f:
        return json.loads(f.read())


@patch('shipit_taskcluster.taskcluster_utils.TC_QUEUE.listTaskGroup', new=mocked_listtaskgroup)
@pytest.mark.parametrize('task_group_id, result', (
    (
        'allcompletedid',
        'completed',
    ),
    (
        'somependingid',
        'running',
    ),
    (
        'somefailedid',
        'failed',
    ),
    (
        'someexceptionid',
        'failed',
    ),
    (
        'badformatid',
        'exception'
    ),
))
def test_get_queue_group_state(task_group_id, result):
    assert get_queue_group_state(task_group_id) == result
