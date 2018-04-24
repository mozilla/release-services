# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from datetime import timedelta

import responses

from shipit_pulse_listener.listener import HookCodeCoverage

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def test_is_coverage_task():
    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    cov_task = {
        'task': {
            'metadata': {
                'name': 'build-linux64-ccov'
            }
        }
    }
    assert hook.is_coverage_task(cov_task)

    cov_task = {
        'task': {
            'metadata': {
                'name': 'build-linux64-ccov/opt'
            }
        }
    }
    assert hook.is_coverage_task(cov_task)

    cov_task = {
        'task': {
            'metadata': {
                'name': 'build-win64-ccov/debug'
            }
        }
    }
    assert hook.is_coverage_task(cov_task)

    nocov_task = {
        'task': {
            'metadata': {
                'name': 'test-linux64-ccov/opt-mochitest-1'
            }
        }
    }
    assert not hook.is_coverage_task(nocov_task)

    nocov_task = {
        'task': {
            'metadata': {
                'name': 'test-linux64/opt-mochitest-1'
            }
        }
    }
    assert not hook.is_coverage_task(nocov_task)


def test_is_old_task():
    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    new_task = {
        'status': {
            'runs': [{
                'resolved': datetime.utcnow().strftime('%Y-%m-%d'),
            }]
        }
    }
    assert not hook.is_old_task(new_task)

    old_task = {
        'status': {
            'runs': [{
                'resolved': (datetime.utcnow() - timedelta(2)).strftime('%Y-%m-%d'),
            }]
        }
    }
    assert hook.is_old_task(old_task)

    old_task = {
        'status': {
            'runs': [{
                'resolved': '2017-07-31T19:32:04.855Z',
            }]
        }
    }
    assert hook.is_old_task(old_task)


def test_get_build_task_in_group():
    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    hook.triggered_groups.add('already-triggered-group')

    assert hook.get_build_task_in_group('already-triggered-group') is None


def test_parse():
    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    hook.triggered_groups.add('already-triggered-group')

    assert hook.parse({
        'taskGroupId': 'already-triggered-group'
    }) is None


def test_is_mozilla_central_task():
    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    inbound_task = {
        'task': {
            'payload': {
                'env': {
                    'MH_BRANCH': 'mozilla-inbound',
                }
            }
        }
    }
    assert not hook.is_mozilla_central_task(inbound_task)

    try_task = {
        'task': {
            'payload': {
                'env': {
                    'MH_BRANCH': 'try',
                }
            }
        }
    }
    assert not hook.is_mozilla_central_task(try_task)

    central_task = {
        'task': {
            'payload': {
                'env': {
                    'MH_BRANCH': 'mozilla-central',
                }
            }
        }
    }
    assert hook.is_mozilla_central_task(central_task)


@responses.activate
def test_wrong_branch():
    with open(os.path.join(FIXTURES_DIR, 'bNq-VIT-Q12o6nXcaUmYNQ.json')) as f:
        responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/bNq-VIT-Q12o6nXcaUmYNQ/list?limit=200', json=json.load(f), status=200, match_querystring=True)  # noqa

    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    assert hook.parse({
        'taskGroupId': 'bNq-VIT-Q12o6nXcaUmYNQ'
    }) is None


@responses.activate
def test_success():
    with open(os.path.join(FIXTURES_DIR, 'RS0UwZahQ_qAcdZzEb_Y9g.json')) as f:

        # Update resolved date
        mockup = json.load(f)
        now = datetime.now().isoformat()
        for i, task in enumerate(mockup['tasks']):
            mockup['tasks'][i]['status']['runs'][0]['resolved'] = now

        responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/RS0UwZahQ_qAcdZzEb_Y9g/list?limit=200', json=mockup, status=200, match_querystring=True)  # noqa

    hook = HookCodeCoverage({
      'hookId': 'shipit-staging-code-coverage'
    })

    assert hook.parse({
        'taskGroupId': 'RS0UwZahQ_qAcdZzEb_Y9g'
    }) == {'REVISION': 'ec3dd3ee2ae4b3a63529a912816a110e925eb2d0'}
