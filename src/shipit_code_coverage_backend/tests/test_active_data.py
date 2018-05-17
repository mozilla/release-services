# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.mark.asyncio
async def test_available_revisions(mock_secrets, mock_active_data):
    '''
    Test last available revisions from Elastic Search cluster
    '''
    from shipit_code_coverage_backend import coverage
    activeDataCoverage = coverage.ActiveDataCoverage()
    revs = await activeDataCoverage.available_revisions()

    assert len(revs) == 2
    assert revs[0]['key'] == '2d83e1843241d869a2fc5cf06f96d3af44c70e70'
    assert revs[1]['key'] == 'a0f7e5f1bea6466277ba96a2bd22eee6f72930c3'


@pytest.mark.asyncio
async def test_latest_build(mock_secrets, mock_active_data):
    '''
    Test latest build availables from Elastic Search cluster
    '''
    from shipit_code_coverage_backend import coverage
    activeDataCoverage = coverage.ActiveDataCoverage()
    latest_rev, previous_rev = await activeDataCoverage.get_latest_build()

    assert latest_rev == '2d83e1843241d869a2fc5cf06f96d3af44c70e70'
    assert previous_rev == 'a0f7e5f1bea6466277ba96a2bd22eee6f72930c3'


@pytest.mark.asyncio
async def test_list_tests_invalid(mock_secrets, mock_active_data):
    '''
    Test latest build availables from Elastic Search cluster
    '''
    from shipit_code_coverage_backend import coverage
    activeDataCoverage = coverage.ActiveDataCoverage()

    nb, tests = await activeDataCoverage.list_tests('dummy', 'test.cpp')
    assert nb == 0
    assert tests == []


@pytest.mark.asyncio
async def test_list_tests_valid(mock_secrets, mock_active_data):
    '''
    Test latest build availables from Elastic Search cluster
    '''
    from shipit_code_coverage_backend import coverage
    activeDataCoverage = coverage.ActiveDataCoverage()

    nb, tests = await activeDataCoverage.list_tests('2d83e1843241d869a2fc5cf06f96d3af44c70e70', 'js/src/jsutil.cpp')
    assert nb == 2
    assert len(tests) == 2
    assert [
        t['_source']['source']['file']['percentage_covered']['~n~']
        for t in tests
    ] == [0.42, 0.1136363636363636, ]


@pytest.mark.asyncio
async def test_file_coverage(mock_secrets, mock_active_data):
    '''
    Test file coverage API from Elastic Search cluster
    '''
    from shipit_code_coverage_backend import coverage
    activeDataCoverage = coverage.ActiveDataCoverage()

    file_coverage = await activeDataCoverage.get_file_coverage('2d83e1843241d869a2fc5cf06f96d3af44c70e70', 'js/src/jsutil.cpp')
    assert isinstance(file_coverage, dict)
    assert file_coverage == {42: 1, 53: 2, 54: 2, 58: 2, 59: 2, 60: 2, 170: 2, 172: 2, 173: 2, 176: 2, 180: 1}
