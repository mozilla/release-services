# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import abort

from cli_common import log
from codecoverage_backend.v2.base import NoResults
from codecoverage_backend.v2.base import active_data
from codecoverage_backend.v2.path import coverage_paths

logger = log.get_logger(__name__)


def coverage_for_path(path='', changeset=None):
    '''
    Aggregate coverage for a path, regardless of its type:
    * file, gives its coverage percent
    * directory, gives coverage percent for its direct sub elements
      files and folders (recursive average)
    '''
    assert active_data.enabled, \
        'Only ActiveData is supported'

    # Fallback to latest changeset
    if changeset is None:
        changeset = active_data.get_latest_changeset()
        assert changeset is not None, 'Missing changeset'
        logger.info('Latest changeset', rev=changeset)

    # Load tests data from ES
    try:
        paths = coverage_paths(path, changeset)
    except NoResults:
        abort(404)

    # Special case for a direct file
    # Output directly the result
    if len(paths) == 1 and paths[0]['type'] == 'file':
        return paths[0]

    # Default case is full directory
    return {
        'type': 'directory',
        'children': paths
    }
