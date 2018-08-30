# -*- coding: utf-8 -*-
import json
import os
import sqlite3
import tarfile

import pytest
import responses

from shipit_code_coverage import chunk_mapping


@pytest.fixture
def fake_artifacts_handler(grcov_artifact, jsvm_artifact, grcov_existing_file_artifact, grcov_uncovered_function_artifact):
    class FakeArtifactsHandler(object):
        def __init__(self):
            pass

        def get_chunks(self):
            return ['chunk1', 'chunk2']

        def get(self, platform=None, suite=None, chunk=None):
            if platform == 'linux' and chunk == 'chunk1':
                return [grcov_artifact]  # js/src/jit/BitSet.cpp
            elif platform == 'linux' and chunk == 'chunk2':
                return [jsvm_artifact]  # toolkit/components/osfile/osfile.jsm
            elif platform == 'windows' and chunk == 'chunk1':
                return [grcov_existing_file_artifact]  # shipit_code_coverage/cli.py
            elif platform == 'windows' and chunk == 'chunk2':
                return [grcov_uncovered_function_artifact]  # js/src/jit/JIT.cpp

    return FakeArtifactsHandler()


def assert_file_to_test(c, source_path, test_path):
    c.execute('SELECT test FROM file_to_test WHERE source=?', (source_path,))
    results = c.fetchall()
    assert len(results) == 1
    assert results[0][0] == test_path


def assert_file_to_chunk(c, path, platform, chunk):
    c.execute('SELECT platform, chunk FROM file_to_chunk WHERE path=?', (path,))
    results = c.fetchall()
    assert len(results) == 1
    assert results[0][0] == platform
    assert results[0][1] == chunk


def assert_chunk_to_test(c, platform, chunk, tests):
    c.execute('SELECT path FROM chunk_to_test WHERE platform=? AND chunk=?', (platform, chunk))
    results = c.fetchall()
    assert len(results) == len(tests)
    assert set([e[0] for e in results]) == set(tests)


@responses.activate
def test_zero_coverage(tmpdir, fake_artifacts_handler, fake_hg_repo):
    tmp_path = tmpdir.strpath

    def request_callback(request):
        payload = json.loads(request.body.decode('utf-8'))

        print(payload)

        if payload['from'] == 'coverage':
            if 'groupby' in payload:
                if payload['groupby'] == ['test.suite']:
                    data = [
                        ['chrome', 2],
                        ['jsreftest', 1],
                    ]
                elif payload['groupby'] == ['test.name']:
                    assert payload['where']['and'][4]['in']['test.suite'] == ['chrome', 'jsreftest']
                    data = [
                        ['js/xpconnect/tests/unit/test_lazyproxy.js', 60],
                        ['netwerk/test/unit/test_substituting_protocol_handler.js', 55],
                    ]
                else:
                    assert False, 'Unexpected groupby'
            elif 'select' in payload:
                if payload['select'] == ['source.file.name', 'test.name']:
                    data = {
                        'source.file.name': [
                            'js/src/vm/TraceLogging.cpp',
                            'gfx/skia/skia/src/pathops/SkPathOpsQuad.cpp',
                        ],
                        'test.name': [
                            'js/xpconnect/tests/unit/test_lazyproxy.js',
                            'netwerk/test/unit/test_substituting_protocol_handler.js',
                        ],
                    }
                else:
                    assert False, 'Unexpected select'
            else:
                assert False, 'Unexpected payload'
        elif payload['from'] == 'unittest':
            if 'groupby' in payload:
                if payload['groupby'] == ['run.suite.fullname']:
                    data = [
                        ['marionette', 3590],
                        ['gtest', 2078],
                        ['talos', 3000],
                    ]
                else:
                    assert False, 'Unexpected groupby'
            elif 'select' in payload:
                if payload['select'] == ['result.test', 'run.key']:
                    requested_suite = payload['where']['and'][2]['eq']['run.suite.fullname']
                    if requested_suite == 'gtest':
                        data = {}
                    elif requested_suite == 'marionette':
                        prefix = payload['where']['and'][3]['prefix']['run.key']
                        if prefix == 'test-linux64-ccov':
                            data = {
                                'result.test': [
                                    'marionette-test1',
                                ],
                                'run.key': [
                                    'test-linux64-ccov/debug-marionette-headless-e10s',
                                ],
                            }
                        elif prefix == 'test-windows10-64-ccov':
                            data = {
                                'result.test': [
                                    'marionette-test2',
                                ],
                                'run.key': [
                                    'test-windows10-64-ccov/debug-marionette-e10s',
                                ],
                            }
                        else:
                            assert False, 'Unexpected prefix'
                    else:
                        assert False, 'Unexpected suite'
                else:
                    assert False, 'Unexpected select'
            else:
                assert False, 'Unexpected payload'
        else:
            assert False, 'Unexpected from'

        return (200, {}, json.dumps({'data': data}))

    responses.add_callback(
        responses.POST, chunk_mapping.ACTIVEDATA_QUERY_URL,
        callback=request_callback,
        content_type='application/json',
    )

    chunk_mapping.generate(
        fake_hg_repo,
        '632bb768b1dd4b96a196412e8f7b669ca09d6d91',
        fake_artifacts_handler,
        out_dir=tmp_path,
    )

    with tarfile.open(os.path.join(tmp_path, 'chunk_mapping.tar.xz')) as t:
        t.extract('chunk_mapping.sqlite', tmp_path)

    with sqlite3.connect(os.path.join(tmp_path, 'chunk_mapping.sqlite')) as conn:
        c = conn.cursor()

        assert_file_to_test(c, 'js/src/vm/TraceLogging.cpp', 'js/xpconnect/tests/unit/test_lazyproxy.js')
        assert_file_to_test(c, 'gfx/skia/skia/src/pathops/SkPathOpsQuad.cpp', 'netwerk/test/unit/test_substituting_protocol_handler.js')

        assert_file_to_chunk(c, 'js/src/jit/BitSet.cpp', 'linux', 'chunk1')
        assert_file_to_chunk(c, 'toolkit/components/osfile/osfile.jsm', 'linux', 'chunk2')
        assert_file_to_chunk(c, 'shipit_code_coverage/cli.py', 'windows', 'chunk1')
        assert_file_to_chunk(c, 'js/src/jit/JIT.cpp', 'windows', 'chunk2')

        assert_chunk_to_test(c, 'linux', 'marionette-headless', ['marionette-test1'])
        assert_chunk_to_test(c, 'windows', 'marionette', ['marionette-test2'])
