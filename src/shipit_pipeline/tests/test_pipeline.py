# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest.mock import MagicMock

import pytest
import requests

from shipit_pipeline.pipeline import PipelineStep
from shipit_pipeline.pipeline import get_runnable_steps
from shipit_pipeline.pipeline import refresh_pipeline_steps


@pytest.fixture
def pipeline_steps():
    pipeline_steps_ = [
      {
        'api_url': 'http://localhost:5001/signoff1',
        'description': 'signoff 1',
        'parameters': {
        },
        'parameters_schema': 'https://null',
        'requires': [
        ],
        'uid': 'signoff1'
      }, {
        'api_url': 'http://localhost:5001/signoff2',
        'description': 'signoff 2 - relman gatekeeps all the things',
        'parameters': {
        },
        'parameters_schema': 'https://null',
        'requires': [
          'signoff1'
        ],
        'uid': 'signoff2'
      }, {
        'api_url': 'http://localhost:5001/publish1',
        'description': 'final publish',
        'parameters': {
        },
        'parameters_schema': 'https://null',
        'requires': [
          'signoff2'
        ],
        'uid': 'publish1'
      }
    ]
    return [PipelineStep.from_dict(step) for step in pipeline_steps_]


def test_get_runnable_steps_when_nothing_has_started(pipeline_steps):
    runnables = get_runnable_steps(pipeline_steps)
    assert len(runnables) == 1
    assert runnables[0].uid == 'signoff1'


def test_get_runnable_steps_state_changed(pipeline_steps):
    pipeline_steps[0].state = 'completed'
    runnables = get_runnable_steps(pipeline_steps)
    assert len(runnables) == 1
    assert runnables[0].uid == 'signoff2'


def test_get_runnable_steps_dependency_in_failure(pipeline_steps):
    pipeline_steps[0].state = 'exception'
    runnables = get_runnable_steps(pipeline_steps)
    assert len(runnables) == 0


def test_get_runnable_steps_state_changed2(pipeline_steps):
    pipeline_steps[0].state = 'completed'
    pipeline_steps[1].state = 'completed'
    runnables = get_runnable_steps(pipeline_steps)
    assert len(runnables) == 1
    assert runnables[0].uid == 'publish1'


def test_get_runnable_steps_many_can_run_at_the_beginning(pipeline_steps):
    another_first_step = PipelineStep(uid='parallel_action_to_signoff1', url='http://null', params={}, requires=[])
    pipeline_steps.append(another_first_step)
    runnables = get_runnable_steps(pipeline_steps)
    assert [r.uid for r in runnables] == ['signoff1', 'parallel_action_to_signoff1']


def test_get_runnable_steps_many_upstream_dependencies(pipeline_steps):
    upstream_dep = PipelineStep(uid='upstream_dep', url='http://null', params={}, requires=[])
    upstream_dep.state = 'completed'
    pipeline_steps[1].requires.append(upstream_dep.uid)
    pipeline_steps.append(upstream_dep)

    runnables = get_runnable_steps(pipeline_steps)
    assert [r.uid for r in runnables] == ['signoff1']

    pipeline_steps[0].state = 'completed'
    runnables = get_runnable_steps(pipeline_steps)
    assert [r.uid for r in runnables] == ['signoff2']


def test_get_runnable_steps_many_many_downstream_deps_run(pipeline_steps):
    downstream_dep = PipelineStep(uid='another_downstream_dep', url='http://null', params={}, requires=[])
    pipeline_steps.append(downstream_dep)

    pipeline_steps[0].state = 'completed'
    runnables = get_runnable_steps(pipeline_steps)
    assert [r.uid for r in runnables] == ['signoff2', 'another_downstream_dep']


def test_refresh_pipeline_steps(pipeline_steps, monkeypatch):
    def mock_get_request(url, verify):
        get_response = MagicMock()
        get_response.json.return_value = {'state': 'completed'} if 'signoff1' in url else {'state': 'busted'}
        return get_response

    monkeypatch.setattr(requests, 'get', mock_get_request)

    pipeline_steps[0].state = 'running'
    pipeline_steps = refresh_pipeline_steps(pipeline_steps)
    assert pipeline_steps[0].state == 'completed'
    assert pipeline_steps[1].state == 'pending'
    assert pipeline_steps[2].state == 'pending'
