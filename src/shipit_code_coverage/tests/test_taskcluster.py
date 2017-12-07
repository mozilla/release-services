# -*- coding: utf-8 -*-

from shipit_code_coverage import taskcluster


def test_last_task():
    assert taskcluster.get_last_task('linux') is not None
    assert taskcluster.get_last_task('win') is not None


def test_get_task_details():
    task_id = taskcluster.get_last_task('linux')
    task_data = taskcluster.get_task_details(task_id)
    assert task_data is not None
    assert 'payload' in task_data


def test_get_task():
    task_id = taskcluster.get_last_task('linux')
    task_data = taskcluster.get_task_details(task_id)
    revision = task_data['payload']['env']['GECKO_HEAD_REV']
    assert taskcluster.get_task('mozilla-central', revision, 'linux') == taskcluster.get_last_task('linux')

    task_id = taskcluster.get_last_task('win')
    task_data = taskcluster.get_task_details(task_id)
    revision = task_data['payload']['env']['GECKO_HEAD_REV']
    assert taskcluster.get_task('mozilla-central', revision, 'win') == taskcluster.get_last_task('win')


def test_get_task_artifacts():
    task_id = taskcluster.get_last_task('linux')
    artifacts = taskcluster.get_task_artifacts(task_id)
    assert len(artifacts) > 0


def test_get_tasks_in_group():
    task_id = taskcluster.get_last_task('linux')
    task_data = taskcluster.get_task_details(task_id)
    tasks = taskcluster.get_tasks_in_group(task_data['taskGroupId'])
    assert len(tasks) > 0


def test_is_coverage_task():
    cov_task = {
        'task': {
            'metadata': {
                'name': 'test-linux64-ccov/opt-mochitest-1'
            }
        }
    }
    assert taskcluster.is_coverage_task(cov_task)

    nocov_task = {
        'task': {
            'metadata': {
                'name': 'test-linux64/opt-mochitest-1'
            }
        }
    }
    assert not taskcluster.is_coverage_task(nocov_task)

    cov_task = {
        'task': {
            'metadata': {
                'name': 'test-windows10-64-ccov/debug-cppunit'
            }
        }
    }
    assert taskcluster.is_coverage_task(cov_task)

    nocov_task = {
        'task': {
            'metadata': {
                'name': 'test-windows10-64/debug-cppunit'
            }
        }
    }
    assert not taskcluster.is_coverage_task(nocov_task)


def test_get_suite_name():
    tests = [
        ('test-linux64-ccov/opt-mochitest-1', 'mochitest'),
        ('test-linux64-ccov/opt-mochitest-e10s-7', 'mochitest'),
        ('test-linux64-ccov/opt-cppunit', 'cppunit'),
        ('test-linux64-ccov/opt-firefox-ui-functional-remote-e10s', 'firefox-ui-functional-remote'),
        ('test-windows10-64-ccov/debug-mochitest-1', 'mochitest'),
        ('test-windows10-64-ccov/debug-mochitest-e10s-7', 'mochitest'),
        ('test-windows10-64-ccov/debug-cppunit', 'cppunit'),
    ]

    for (name, suite) in tests:
        task = {
            'task': {
                'metadata': {
                    'name': name
                }
            }
        }

        assert taskcluster.get_suite_name(task) == suite
