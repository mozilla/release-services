# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from cli_common import log
from flask import abort
import asyncio
from shipit_code_coverage_backend.v2.base import active_data, NoResults
from shipit_code_coverage_backend.v2.path import coverage_paths
from shipit_code_coverage_backend.v2.diff import coverage_diff, load_raw_patch

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


def coverage_for_revision(changeset):
    '''
    List coverage changes for any revision
    '''
    assert active_data.enabled, \
        'Only ActiveData is supported'

    # Run slow tasks in parallel
    loop = asyncio.get_event_loop()
    patch, revision = loop.run_until_complete(asyncio.gather(

        # Load raw patch data from hgweb
        load_raw_patch(changeset),

        # Load coverage for this changeset modifications
        coverage_diff(changeset)
    ))
    loop.close()

    # Output nicely all data
    return {
        'patch': patch,
        'changeset': {
            'author': revision['changeset']['author'],
            'bug': revision['changeset']['bug'],
            'date': revision['changeset']['date'],
            'description': revision['changeset']['description'],
            'mercurial': {
                'hash': revision['changeset']['id'],
                'repo': revision['branch']['url'],
                'index': revision['index'],
            },
            'push': revision['push']['id'],
        },
        'coverage': revision['coverage'],
    }
