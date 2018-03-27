# -*- coding: utf-8 -*-

import os
from shipit_code_coverage.artifacts import ArtifactsHandler
from unittest.mock import patch
import pytest


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


@responses.activate
def test_download(LINUX_TASK_ID, LINUX_TASK_ARTIFACTS, FAKE_ARTIFACTS_DIR):
    #I want to use this to write the paths of files downloaded.
    def add_dir(files):
        return set([os.path.join(FAKE_ARTIFACTS_DIR, f) for f in files])

    a = ArtifactsHandler([], [], parent_dir=FAKE_ARTIFACTS_DIR)

    #mock the taskcluster.get_task_artifacts()
    responses.add(responses.GET, 'https://queue.taskcluster.net/v1/task/{}/artifacts'.format(LINUX_TASK_ID), json=LINUX_TASK_ARTIFACTS, status=200)
    a.download(TEST_TASK)
    #I want to mock the taskcluster.download_artifact()
    responses.add(response.GET, queue_base + 'task/{}/artifacts/{}'.format(TEST_TASK['taskId'], TEST_TASK['name'), )
