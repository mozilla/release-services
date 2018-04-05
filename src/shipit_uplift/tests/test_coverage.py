# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import responses
from shipit_uplift import (
    coverage_by_changeset_impl, coverage_summary_by_changeset_impl,
    coverage_for_file_impl
)


def test_coverage_supported_extensions_api(client):
    # List supported extensions for coverage analysis through the API
    resp = client.get('/coverage/supported_extensions')
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert set(data) == set([
        'c', 'h', 'cpp', 'cc', 'cxx', 'hh', 'hpp',
        'hxx', 'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
    ])


@responses.activate
def test_coverage_latest_api(client, coverage_responses):
    resp = client.get('/coverage/latest')
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert data['latest_rev'] == '8063b0c54b888fe1f98774b71e1870cc2267f33f'
    assert data['latest_pushid'] == 33743
    assert data['previous_rev'] == '5401938bde37d0e7f1016bbd7694e72bdbf5e9a1'


@responses.activate
def test_coverage_by_changeset_impl(coverage_responses, coverage_builds):
    # Get changeset coverage information
    for changeset in coverage_builds['info']:
        data = coverage_by_changeset_impl.generate(changeset)
        assert data == coverage_builds['info'][changeset]


@responses.activate
def test_coverage_summary_by_changeset_impl(coverage_responses, coverage_builds):
    # Get changeset coverage summary from coverage information
    for changeset in coverage_builds['summary']:
        coverage_data = coverage_builds['info'][changeset]
        summary = coverage_summary_by_changeset_impl.generate(coverage_data)
        assert summary == coverage_builds['summary'][changeset]


@responses.activate
def test_coverage_for_file_impl(coverage_responses, coverage_changeset_by_file):
    # Get code coverage information for a given file at a given changeset
    for file_coverage in coverage_changeset_by_file:
        data = coverage_for_file_impl.generate(file_coverage['changeset'], file_coverage['path'])
        assert data == file_coverage['data']
