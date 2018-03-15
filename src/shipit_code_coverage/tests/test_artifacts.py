# -*- coding: utf-8 -*-

import os
from shipit_code_coverage.artifacts import ArtifactsHandler
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
