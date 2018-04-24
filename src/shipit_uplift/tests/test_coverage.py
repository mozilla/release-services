# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

from shipit_uplift import coverage
from shipit_uplift import coverage_by_changeset_impl
from shipit_uplift import coverage_for_file_impl
from shipit_uplift import coverage_summary_by_changeset_impl


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
    data = await coverage.get_latest_build_info()
    assert data['latest_rev'] == '8063b0c54b888fe1f98774b71e1870cc2267f33f'
    assert data['latest_pushid'] == 33743
    assert data['previous_rev'] == '5401938bde37d0e7f1016bbd7694e72bdbf5e9a1'


@pytest.mark.asyncio
async def test_coverage_by_changeset_impl(coverage_responses, coverage_builds):
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
    # Get changeset coverage summary from coverage information
    for changeset, expected in coverage_builds['summary'].items():
        coverage_data = coverage_builds['info'][changeset]
        summary = coverage_summary_by_changeset_impl.generate(coverage_data)
        assert summary == expected


@pytest.mark.asyncio
async def test_coverage_for_file_impl(coverage_responses, coverage_changeset_by_file):
    # Get code coverage information for a given file at a given changeset
    for file_coverage in coverage_changeset_by_file:
        data = await coverage_for_file_impl.generate(file_coverage['changeset'], file_coverage['path'])
        assert data['data'] == file_coverage['data']
        assert data['build_changeset'] == file_coverage['build_changeset']
        assert data['git_build_changeset'] == file_coverage['git_build_changeset']


@pytest.mark.asyncio
async def test_skip_broken_build(coverage_responses):
    codecovCoverage = coverage.CodecovCoverage()

    with pytest.raises(coverage.CoverageException, message='ee6283795f41d97faeaccbe8bd051a36bbe30c64 is in an errored state.'):
        await codecovCoverage.get_coverage('ee6283795f41d97faeaccbe8bd051a36bbe30c64')

    with pytest.raises(coverage.CoverageException, message='ee6283795f41d97faeaccbe8bd051a36bbe30c64 is in an errored state.'):
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
