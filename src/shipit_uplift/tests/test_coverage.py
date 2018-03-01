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
    '''
    List supported extensions for coverage analysis through api
    '''
    resp = client.get('/coverage/supported_extensions')
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    assert set(data) == set([
        'c', 'h', 'cpp', 'cc', 'cxx', 'hh', 'hpp',
        'hxx', 'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
    ])


@responses.activate
def disable_test_coverage_by_changeset_impl(client, coverage_builds):
    '''
    Get changeset coverage information from the internet
    '''
    responses.add_passthru('https://hg.mozilla.org/mozilla-central/')
    responses.add_passthru('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev')
    responses.add_passthru('https://codecov.io/api/gh/marco-c/gecko-dev')
    for changeset in coverage_builds['info']:
        data = coverage_by_changeset_impl.generate(changeset)
        assert data == coverage_builds['info'][changeset]


def test_coverage_summary_by_changeset_impl(client, coverage_builds):
    '''
    Get changeset coverage summary from coverage information
    '''
    for changeset in coverage_builds['summary']:
        coverage_data = coverage_builds['info'][changeset]
        summary = coverage_summary_by_changeset_impl.generate(coverage_data)
        assert summary == coverage_builds['summary'][changeset]


@responses.activate
def disable_test_coverage_for_file_impl(client, coverage_changeset_by_file):
    '''
    Get code coverage information for a given file at a given changeset, from the internet
    '''
    responses.add_passthru('https://hg.mozilla.org/mozilla-central/')
    responses.add_passthru('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev')
    responses.add_passthru('https://codecov.io/api/gh/marco-c/gecko-dev')
    for file_coverage in coverage_changeset_by_file:
        data = coverage_for_file_impl.generate(file_coverage['changeset'], file_coverage['path'])
        assert data == file_coverage['data']
