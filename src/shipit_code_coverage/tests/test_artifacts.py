# -*- coding: utf-8 -*-

import os
from cli_common import utils
from shipit_code_coverage.artifacts import ArtifactsHandler


FILES = ['ccov-artifacts/%s' % f for f in [
    'windows_mochitest-1_code-coverage-jsvm.info',
    'linux_mochitest-2_code-coverage-grcov.zip',
    'windows_xpcshell-7_code-coverage-jsvm.info',
    'linux_xpcshell-7_code-coverage-grcov.zip',
    'linux_xpcshell-3_code-coverage-grcov.zip',
    'windows_cppunit_code-coverage-grcov.zip',
    'linux_firefox-ui-functional-remote_code-coverage-jsvm.info',
]]


def test_get_chunks():
    utils.mkdir('ccov-artifacts')

    for f in FILES:
        open(f, 'w')

    a = ArtifactsHandler([], [])
    assert set(a.get_chunks()) == set([
        'mochitest-1', 'mochitest-2', 'xpcshell-3', 'xpcshell-7',
        'cppunit', 'firefox-ui-functional-remote',
    ])

    for f in FILES:
        os.remove(f)


def test_get_coverage_artifacts():
    utils.mkdir('ccov-artifacts')

    for f in FILES:
        open(f, 'w')

    a = ArtifactsHandler([], [])
    assert set(a.get()) == set(FILES)
    assert set(a.get(suite='mochitest')) == set([
        'ccov-artifacts/windows_mochitest-1_code-coverage-jsvm.info',
        'ccov-artifacts/linux_mochitest-2_code-coverage-grcov.zip'
    ])
    assert set(a.get(chunk='xpcshell-7')) == set([
        'ccov-artifacts/windows_xpcshell-7_code-coverage-jsvm.info',
        'ccov-artifacts/linux_xpcshell-7_code-coverage-grcov.zip'
    ])
    assert set(a.get(chunk='cppunit')) == set([
        'ccov-artifacts/windows_cppunit_code-coverage-grcov.zip'
    ])
    assert set(a.get(platform='windows')) == set([
        'ccov-artifacts/windows_mochitest-1_code-coverage-jsvm.info',
        'ccov-artifacts/windows_xpcshell-7_code-coverage-jsvm.info',
        'ccov-artifacts/windows_cppunit_code-coverage-grcov.zip',
    ])
    assert set(a.get(platform='linux', chunk='xpcshell-7')) == set([
        'ccov-artifacts/linux_xpcshell-7_code-coverage-grcov.zip'
    ])

    try:
        a.get(chunk='xpcshell-7', suite='mochitest')
        assert False, 'An exception should have been thrown'
    except:
        pass

    for f in FILES:
        os.remove(f)
