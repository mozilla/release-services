# -*- coding: utf-8 -*-

import os
from shipit_code_coverage.artifacts import ArtifactsHandler
from unittest import mock
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


@mock.patch('shipit_code_coverage.taskcluster.get_task_artifacts')
@mock.patch('shipit_code_coverage.taskcluster.download_artifact')
def test_download(mocked_download_artifact, mocked_get_task, LINUX_TEST_TASK_ARTIFACTS):
    a = ArtifactsHandler([], [], [])
    mocked_get_task.return_value = LINUX_TEST_TASK_ARTIFACTS['artifacts']
    mocked_download_artifact.return_value = LINUX_TEST_TASK_ARTIFACTS['artifacts'][0]

    a.download(LINUX_TEST_TASK_ARTIFACTS)

    assert mocked_download_artifact.call_count == 1
    assert mocked_get_task.call_count == 1
    mocked_download_artifact.assert_called_with(
        [
            'l', 'i', 'n', 'u', 'x', '_', 't', 'e', 's', 't', '/',
            'c', 'o', 'd', 'e', '-', 'c', 'o', 'v', 'e', 'r', 'a', 'g',
            'e', '-', 'g', 'r', 'c', 'o', 'v', '.', 'z', 'i', 'p', '_',
            'c', 'o', 'd', 'e', '-', 'c', 'o', 'v', 'e', 'r', 'a', 'g',
            'e', '-', 'g', 'r', 'c', 'o', 'v', '.', 'z', 'i', 'p'
        ],
        'MJIO3RWTRu2GhiE7_jILBw',
        'public/code-coverage-grcov.zip',
    )
