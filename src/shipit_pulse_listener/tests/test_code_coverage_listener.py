# -*- coding: utf-8 -*-
from shipit_pulse_listener.listener import HookCodeCoverage
from datetime import datetime, timedelta


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
