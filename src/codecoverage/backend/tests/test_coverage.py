# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from unittest import mock

import pytest
from fakeredis import FakeStrictRedis
from rq import SimpleWorker


def test_coverage_supported_extensions_api(client):
    # List supported extensions for coverage analysis through the API
    resp = client.get('/coverage/supported_extensions')
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert set(data) == set([
        'c', 'h', 'cpp', 'cc', 'cxx', 'hh', 'hpp',
        'hxx', 'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
    ])


@pytest.mark.asyncio
async def test_coverage_latest(coverage_responses):
    from codecoverage_backend import coverage
    data = await coverage.get_latest_build_info()
    assert data['latest_rev'] == '8063b0c54b888fe1f98774b71e1870cc2267f33f'
    assert data['latest_pushid'] == 33743
    assert data['previous_rev'] == '5401938bde37d0e7f1016bbd7694e72bdbf5e9a1'


def mock_coverage_by_changeset_job_success(job_changeset):
    from tests.conftest import coverage_builds as get_coverage_builds
    coverage_builds = get_coverage_builds()
    for changeset, expected in coverage_builds['info'].items():
        if changeset == job_changeset or changeset[:12] == job_changeset[:12]:
            return expected
    raise NotImplementedError('Not implemented return values for changeset %s' % job_changeset)


def test_coverage_by_changeset(coverage_builds):
    from rq import Queue
    from codecoverage_backend import api

    # patch the queue to be sync to allow it run without workers. http://python-rq.org/docs/testing/
    with mock.patch('codecoverage_backend.api.q', Queue(connection=FakeStrictRedis(singleton=False))) as q:
        # patch the mock_coverage_by_changeset
        with mock.patch('codecoverage_backend.api.coverage_by_changeset_job', mock_coverage_by_changeset_job_success):
            assert q.is_empty()

            # Get changeset coverage information
            for changeset, expected in coverage_builds['info'].items():
                result, code = api.coverage_by_changeset(changeset)
                assert code == 202

            # test that in the case of exception it will return 500
            result, code = api.coverage_by_changeset('mozilla test changeset')
            assert code == 202

            # run simple worker to run all tasks
            w = SimpleWorker([q], connection=q.connection)
            w.work(burst=True)

            # Everything should be 200 now
            for changeset, expected in coverage_builds['info'].items():
                result, code = api.coverage_by_changeset(changeset)
                assert code == 200

            # except the incorrect changeset, should be 500
            result, code = api.coverage_by_changeset('mozilla test changeset')
            assert code == 500


def test_coverage_summary_by_changeset(coverage_builds):
    from rq import Queue
    from codecoverage_backend import api

    # patch the queue to be sync to allow it run without workers. http://python-rq.org/docs/testing/
    with mock.patch('codecoverage_backend.api.q', Queue(connection=FakeStrictRedis())):
        # Get changeset coverage information
        for changeset, expected in coverage_builds['summary'].items():
            result, code = api.coverage_summary_by_changeset(changeset)
            assert code == 202


@pytest.mark.asyncio
async def test_coverage_by_changeset_impl(coverage_responses, coverage_builds):
    from codecoverage_backend import coverage_by_changeset_impl
    # Get changeset coverage information
    for changeset, expected in coverage_builds['info'].items():
        data = await coverage_by_changeset_impl.generate(changeset)
        assert data['build_changeset'] == expected['build_changeset']
        for diff in data['diffs']:
            exp_diff = None
            for i in expected['diffs']:
                if diff['name'] == i['name']:
                    exp_diff = i
                    break
            assert exp_diff is not None
            assert diff == exp_diff
        assert data['git_build_changeset'] == expected['git_build_changeset']
        assert data['overall_cur'] == expected['overall_cur']
        assert data['overall_prev'] == expected['overall_prev']


def test_coverage_summary_by_changeset_impl(coverage_builds):
    from codecoverage_backend import coverage_summary_by_changeset_impl
    # Get changeset coverage summary from coverage information
    for changeset, expected in coverage_builds['summary'].items():
        coverage_data = coverage_builds['info'][changeset]
        summary = coverage_summary_by_changeset_impl.generate(coverage_data)
        assert summary == expected


@pytest.mark.asyncio
async def test_coverage_for_file_impl(coverage_responses, coverage_changeset_by_file):
    from codecoverage_backend import coverage_for_file_impl
    # Get code coverage information for a given file at a given changeset
    for file_coverage in coverage_changeset_by_file:
        data = await coverage_for_file_impl.generate(file_coverage['changeset'], file_coverage['path'])
        assert data['data'] == file_coverage['data']
        assert data['build_changeset'] == file_coverage['build_changeset']
        assert data['git_build_changeset'] == file_coverage['git_build_changeset']


@pytest.mark.asyncio
async def test_skip_broken_build(coverage_responses):
    from codecoverage_backend.services.codecov import CodecovCoverage
    from codecoverage_backend.services.base import CoverageException
    from codecoverage_backend import coverage
    codecovCoverage = CodecovCoverage()

    with pytest.raises(CoverageException, message='ee6283795f41d97faeaccbe8bd051a36bbe30c64 is in an errored state.'):
        await codecovCoverage.get_coverage('ee6283795f41d97faeaccbe8bd051a36bbe30c64')

    with pytest.raises(CoverageException, message='ee6283795f41d97faeaccbe8bd051a36bbe30c64 is in an errored state.'):
        await codecovCoverage.get_file_coverage('ee6283795f41d97faeaccbe8bd051a36bbe30c64', 'widget/gtk/nsWindow.cpp')

    changeset_data, build_changeset, overall = await coverage.get_coverage_build('ee6283795f41d97faeaccbe8bd051a36bbe30c64')

    # 3ecc48155838ca413a56920d801a8be0719e9981 is the first commit after
    # ee6283795f41d97faeaccbe8bd051a36bbe30c64 not in error state and
    # with coverage data .

    assert changeset_data['merge']
    assert changeset_data['push'] == 33785
    assert build_changeset == '3ecc48155838ca413a56920d801a8be0719e9981'
    assert overall['cur'] == '61.23183'
    assert overall['prev'] == '61.11536'
