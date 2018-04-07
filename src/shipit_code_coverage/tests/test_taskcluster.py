# -*- coding: utf-8 -*-

import os
from unittest import mock
from zipfile import BadZipFile

import pytest
import requests
import responses

from shipit_code_coverage import taskcluster


@responses.activate
def test_last_task_linux(LINUX_TASK_ID, LATEST_LINUX):
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.latest.firefox.linux64-ccov-opt', json=LATEST_LINUX, status=200)  # noqa
    assert taskcluster.get_last_task('linux') == LINUX_TASK_ID


@responses.activate
def test_last_task_windows(WIN_TASK_ID, LATEST_WIN):
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.latest.firefox.win64-ccov-debug', json=LATEST_WIN, status=200)
    assert taskcluster.get_last_task('win') == WIN_TASK_ID


@responses.activate
def test_last_task_failure(TASK_NOT_FOUND):
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.latest.firefox.linux64-ccov-opt', json=TASK_NOT_FOUND, status=404)  # noqa

    with pytest.raises(requests.exceptions.HTTPError):
        taskcluster.get_last_task('linux')


@responses.activate
def test_get_task_status(LINUX_TASK_ID, LINUX_TASK_STATUS):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}/status'.format(LINUX_TASK_ID), json=LINUX_TASK_STATUS, status=200)
    assert taskcluster.get_task_status(LINUX_TASK_ID) == LINUX_TASK_STATUS


@responses.activate
def test_get_task_details(LINUX_TASK_ID, LINUX_TASK):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}'.format(LINUX_TASK_ID), json=LINUX_TASK, status=200)
    assert taskcluster.get_task_details(LINUX_TASK_ID) == LINUX_TASK


@responses.activate
def test_get_task(LINUX_TASK_ID, LATEST_LINUX, WIN_TASK_ID, LATEST_WIN):
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.revision.b2a9a4bb5c94de179ae7a3f52fde58c0e2897498.firefox.linux64-ccov-opt', json=LATEST_LINUX, status=200)  # noqa
    assert taskcluster.get_task('mozilla-central', 'b2a9a4bb5c94de179ae7a3f52fde58c0e2897498', 'linux') == LINUX_TASK_ID

    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.revision.916103b8675d9fdb28b891cac235d74f9f475942.firefox.win64-ccov-debug', json=LATEST_WIN, status=200)  # noqa
    assert taskcluster.get_task('mozilla-central', '916103b8675d9fdb28b891cac235d74f9f475942', 'win') == WIN_TASK_ID


@responses.activate
def test_get_task_not_found(TASK_NOT_FOUND):
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.revision.b2a9a4bb5c94de179ae7a3f52fde58c0e2897498.firefox.linux64-ccov-opt', json=TASK_NOT_FOUND, status=404)  # noqa

    with pytest.raises(Exception, message='Code coverage build failed and was not indexed.'):
        taskcluster.get_task('mozilla-central', 'b2a9a4bb5c94de179ae7a3f52fde58c0e2897498', 'linux')


@responses.activate
def test_get_task_failure(TASK_NOT_FOUND):
    err = TASK_NOT_FOUND.copy()
    err['code'] = 'RandomError'
    responses.add(responses.GET, 'https://index.taskcluster.net/v1/task/gecko.v2.mozilla-central.revision.b2a9a4bb5c94de179ae7a3f52fde58c0e2897498.firefox.linux64-ccov-opt', json=err, status=500)  # noqa

    with pytest.raises(Exception, message='Unknown TaskCluster index error.'):
        taskcluster.get_task('mozilla-central', 'b2a9a4bb5c94de179ae7a3f52fde58c0e2897498', 'linux')


@responses.activate
def test_get_task_artifacts(LINUX_TASK_ID, LINUX_TASK_ARTIFACTS):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}/artifacts'.format(LINUX_TASK_ID), json=LINUX_TASK_ARTIFACTS, status=200)
    assert taskcluster.get_task_artifacts(LINUX_TASK_ID) == LINUX_TASK_ARTIFACTS['artifacts']


@responses.activate
def test_get_tasks_in_group(GROUP_TASKS_1, GROUP_TASKS_2):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/aPt9FbIdQwmhwDIPDYLuaw/list?limit=200', json=GROUP_TASKS_1, status=200, match_querystring=True)  # noqa
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task-group/aPt9FbIdQwmhwDIPDYLuaw/list?continuationToken=1%2132%21YVB0OUZiSWRRd21od0RJUERZTHVhdw--~1%2132%21ZnJVcGRRT0VTalN0Nm9Ua1Ztcy04UQ--&limit=200', json=GROUP_TASKS_2, status=200, match_querystring=True)  # noqa

    assert taskcluster.get_tasks_in_group('aPt9FbIdQwmhwDIPDYLuaw') == GROUP_TASKS_1['tasks'] + GROUP_TASKS_2['tasks']


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


def test_get_chunk():
    tests = [
        ('test-linux64-ccov/opt-mochitest-1', 'mochitest-1'),
        ('test-linux64-ccov/opt-mochitest-e10s-7', 'mochitest-7'),
        ('test-linux64-ccov/opt-cppunit', 'cppunit'),
        ('test-linux64-ccov/opt-firefox-ui-functional-remote-e10s', 'firefox-ui-functional-remote'),
        ('test-windows10-64-ccov/debug-mochitest-1', 'mochitest-1'),
        ('test-windows10-64-ccov/debug-mochitest-e10s-7', 'mochitest-7'),
        ('test-windows10-64-ccov/debug-cppunit', 'cppunit'),
    ]

    for (name, chunk) in tests:
        assert taskcluster.get_chunk(name) == chunk


def test_get_suite():
    tests = [
        ('mochitest-1', 'mochitest'),
        ('mochitest-7', 'mochitest'),
        ('cppunit', 'cppunit'),
        ('firefox-ui-functional-remote', 'firefox-ui-functional-remote'),
    ]

    for (chunk, suite) in tests:
        assert taskcluster.get_suite(chunk) == suite


def test_get_platform():
    tests = [
        ('test-linux64-ccov/opt-mochitest-1', 'linux'),
        ('test-windows10-64-ccov/debug-mochitest-1', 'windows'),
    ]

    for (name, platform) in tests:
        assert taskcluster.get_platform(name) == platform


@mock.patch('time.sleep')
@responses.activate
def test_download_artifact_forbidden(mocked_sleep, tmpdir):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/FBdocjnAQOW_GJDOfmgjxw/artifacts/public/test_info/code-coverage-grcov.zip', body='xml error...', status=403)  # noqa

    with pytest.raises(requests.exceptions.HTTPError, message='403 Client Error: Forbidden for url: https://taskcluster-artifacts.net/FBdocjnAQOW_GJDOfmgjxw/0/public/test_info/code-coverage-grcov.zip'):  # noqa
        taskcluster.download_artifact(
            os.path.join(tmpdir.strpath, 'windows_reftest-6_code-coverage-grcov.zip'),
            'FBdocjnAQOW_GJDOfmgjxw',
            'public/test_info/code-coverage-grcov.zip'
        )

    assert mocked_sleep.call_count == 4


@mock.patch('time.sleep')
@responses.activate
def test_download_artifact_badzip(mocked_sleep, tmpdir):
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/FBdocjnAQOW_GJDOfmgjxw/artifacts/public/test_info/code-coverage-grcov.zip', body='NOT A ZIP FILE', status=200, stream=True)  # noqa

    with pytest.raises(BadZipFile, message='File is not a zip file'):
        taskcluster.download_artifact(
            os.path.join(tmpdir.strpath, 'windows_reftest-6_code-coverage-grcov.zip'),
            'FBdocjnAQOW_GJDOfmgjxw',
            'public/test_info/code-coverage-grcov.zip'
        )

    assert mocked_sleep.call_count == 4
