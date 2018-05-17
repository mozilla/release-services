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
