# -*- coding: utf-8 -*-

import itertools
import os
from unittest import mock

import pytest
import responses

from code_coverage_bot.artifacts import ArtifactsHandler

FILES = [
    'windows_mochitest-1_code-coverage-jsvm.info',
    'linux_mochitest-2_code-coverage-grcov.zip',
    'windows_xpcshell-7_code-coverage-jsvm.info',
    'linux_xpcshell-7_code-coverage-grcov.zip',
    'linux_xpcshell-3_code-coverage-grcov.zip',
    'windows_cppunit_code-coverage-grcov.zip',
    'linux_firefox-ui-functional-remote_code-coverage-jsvm.info',
]


@pytest.fixture
def FAKE_ARTIFACTS_DIR(tmpdir):
    for f in FILES:
        open(os.path.join(tmpdir.strpath, f), 'w')
    return tmpdir.strpath


def test_get_chunks(FAKE_ARTIFACTS_DIR):
    a = ArtifactsHandler([], [], parent_dir=FAKE_ARTIFACTS_DIR)
    assert set(a.get_chunks()) == set([
        'mochitest-1', 'mochitest-2', 'xpcshell-3', 'xpcshell-7',
        'cppunit', 'firefox-ui-functional-remote',
    ])


def test_get_coverage_artifacts(FAKE_ARTIFACTS_DIR):
    def add_dir(files):
        return set([os.path.join(FAKE_ARTIFACTS_DIR, f) for f in files])

    a = ArtifactsHandler([], [], parent_dir=FAKE_ARTIFACTS_DIR)
    assert set(a.get()) == add_dir(FILES)
    assert set(a.get(suite='mochitest')) == add_dir([
        'windows_mochitest-1_code-coverage-jsvm.info',
        'linux_mochitest-2_code-coverage-grcov.zip'
    ])
    assert set(a.get(chunk='xpcshell-7')) == add_dir([
        'windows_xpcshell-7_code-coverage-jsvm.info',
        'linux_xpcshell-7_code-coverage-grcov.zip'
    ])
    assert set(a.get(chunk='cppunit')) == add_dir([
        'windows_cppunit_code-coverage-grcov.zip'
    ])
    assert set(a.get(platform='windows')) == add_dir([
        'windows_mochitest-1_code-coverage-jsvm.info',
        'windows_xpcshell-7_code-coverage-jsvm.info',
        'windows_cppunit_code-coverage-grcov.zip',
    ])
    assert set(a.get(platform='linux', chunk='xpcshell-7')) == add_dir([
        'linux_xpcshell-7_code-coverage-grcov.zip'
    ])

    with pytest.raises(Exception, message='suite and chunk can\'t both have a value'):
        a.get(chunk='xpcshell-7', suite='mochitest')


@mock.patch('code_coverage_bot.taskcluster.get_task_artifacts')
@mock.patch('code_coverage_bot.taskcluster.download_artifact')
def test_download(mocked_download_artifact, mocked_get_task_artifact, TEST_TASK_FROM_GROUP, LINUX_TEST_TASK_ARTIFACTS):
    a = ArtifactsHandler([], [])
    mocked_get_task_artifact.return_value = LINUX_TEST_TASK_ARTIFACTS['artifacts']

    a.download(TEST_TASK_FROM_GROUP)

    assert mocked_get_task_artifact.call_count == 1
    assert mocked_download_artifact.call_count == 2
    assert mocked_download_artifact.call_args_list[0] == mock.call(
        'ccov-artifacts/linux_mochitest-devtools-chrome-4_code-coverage-grcov.zip',
        'AN1M9SW0QY6DZT6suL3zlQ',
        'public/test_info/code-coverage-grcov.zip',
    )
    assert mocked_download_artifact.call_args_list[1] == mock.call(
        'ccov-artifacts/linux_mochitest-devtools-chrome-4_code-coverage-jsvm.zip',
        'AN1M9SW0QY6DZT6suL3zlQ',
        'public/test_info/code-coverage-jsvm.zip',
    )


# In the download_all tests, we want to make sure the relative ordering of the tasks
# in the Taskcluster group does not affect the result, so we test with all possible
# orderings of several possible states.
def _group_tasks():
    task_state_groups = [
        [
            ('test-linux64-ccov/debug-mochitest-devtools-chrome-e10s-4', 'exception'),
            ('test-linux64-ccov/debug-mochitest-devtools-chrome-e10s-4', 'failed'),
            ('test-linux64-ccov/debug-mochitest-devtools-chrome-e10s-4', 'completed'),
        ],
        [
            ('test-linux64-ccov/debug-xpcshell-4', 'exception'),
            ('test-linux64-ccov/debug-xpcshell-4', 'failed'),
        ],
        [
            ('test-windows10-64-ccov/debug-talos-dromaeojs-e10s', 'failed'),
            ('test-windows10-64-ccov/debug-talos-dromaeojs-e10s', 'completed'),
        ],
        [
            ('test-linux64-ccov/debug-cppunit', 'exception'),
            ('test-linux64-ccov/debug-cppunit', 'completed'),
        ],
        [
            ('test-linux64-stylo-disabled/debug-crashtest-e10s', 'completed'),
        ]
    ]

    # Transform a task_name and state into an object like the ones returned by Taskcluster.
    def build_task(task_state):
        task_name = task_state[0]
        state = task_state[1]
        return {
            'status': {
                'taskId': task_name + '-' + state,
                'state': state,
            },
            'task': {
                'metadata': {
                    'name': task_name
                },
            }
        }

    # Generate all possible permutations of task_name - state.
    task_state_groups_permutations = [list(itertools.permutations(task_state_group)) for task_state_group in task_state_groups]

    # Generate the product of all possible permutations.
    for ordering in itertools.product(*task_state_groups_permutations):
        yield {
            'taskGroupId': 'aPt9FbIdQwmhwDIPDYLuaw',
            'tasks': [build_task(task_state) for sublist in ordering for task_state in sublist],
        }


@responses.activate
def test_download_all(LINUX_TASK_ID, LINUX_TASK, GROUP_TASKS_1, GROUP_TASKS_2, FAKE_ARTIFACTS_DIR):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}'.format(LINUX_TASK_ID), json=LINUX_TASK, status=200)
    for group_tasks in _group_tasks():
        responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/aPt9FbIdQwmhwDIPDYLuaw/list', json=group_tasks, status=200)

        a = ArtifactsHandler({'linux': LINUX_TASK_ID}, [], parent_dir=FAKE_ARTIFACTS_DIR)

        downloaded = set()

        def mock_download(task):
            downloaded.add(task['status']['taskId'])
        a.download = mock_download

        a.download_all()

        assert downloaded == set([
            'test-linux64-ccov/debug-mochitest-devtools-chrome-e10s-4-completed',
            'test-linux64-ccov/debug-xpcshell-4-failed',
            'test-windows10-64-ccov/debug-talos-dromaeojs-e10s-completed',
            'test-linux64-ccov/debug-cppunit-completed',
        ])


@responses.activate
def test_download_all_ignore(LINUX_TASK_ID, LINUX_TASK, GROUP_TASKS_1, GROUP_TASKS_2, FAKE_ARTIFACTS_DIR):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}'.format(LINUX_TASK_ID), json=LINUX_TASK, status=200)
    for group_tasks in _group_tasks():
        responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/aPt9FbIdQwmhwDIPDYLuaw/list', json=group_tasks, status=200)

        a = ArtifactsHandler({'linux': LINUX_TASK_ID}, ['talos', 'xpcshell'], parent_dir=FAKE_ARTIFACTS_DIR)

        downloaded = set()

        def mock_download(task):
            downloaded.add(task['status']['taskId'])
        a.download = mock_download

        a.download_all()

        assert downloaded == set([
            'test-linux64-ccov/debug-mochitest-devtools-chrome-e10s-4-completed',
            'test-linux64-ccov/debug-cppunit-completed',
        ])
