# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio

import aiohttp

from shipit_uplift.coverage import coverage_service
from shipit_uplift.coverage import coverage_supported
from shipit_uplift.coverage import get_coverage_build
from shipit_uplift.coverage import get_github_commit


async def generate(changeset):
    '''
    This function generates a report containing the coverage information of the diff
    introduced by a changeset.
    '''
    changeset_data, build_changeset, overall = await get_coverage_build(changeset)
    if 'merge' in changeset_data:
        raise Exception('Retrieving coverage for merge commits is not supported.')

    async def retrieve_coverage(path):
        # If the file is not a source file, we skip it (as we already know
        # we have no coverage information for it).
        if not coverage_supported(path):
            return None

        # Retrieve annotate data.
        async with aiohttp.request('GET', 'https://hg.mozilla.org/mozilla-central/json-annotate/{}/{}'.format(build_changeset, path)) as r:
            annotate_future = r.json()

            # Retrieve coverage data.
            coverage_future = coverage_service.get_file_coverage(build_changeset, path)

            # Use hg annotate to report lines in their correct positions and to avoid
            # reporting lines that have been modified by a successive patch in the same push.
            data = await annotate_future
            if 'not found in manifest' in data:
                # The file was removed.
                return None
            annotate = data['annotate']

            coverage = await coverage_future

        # If we don't have coverage for this file, we skip it.
        if coverage is None:
            return None

        changes = []
        for data in annotate:
            # Skip lines that were not added by this changeset or were overwritten by
            # another changeset.
            if data['node'][:len(changeset)] != changeset:
                continue

            new_line = data['lineno']

            if new_line not in coverage or coverage[new_line] is None:
                # We have no coverage information for this line (e.g. a definition, like
                # a variable in a header file).
                covered = '?'
            elif coverage[new_line] > 0:
                covered = 'Y'
            else:
                covered = 'N'

            changes.append({
                'coverage': covered,
                'line': data['targetline'],
            })

        return {
            'name': path,
            'changes': changes,
        }

    futures = []
    for path in changeset_data['files']:
        futures.append(retrieve_coverage(path))

    diffs = []
    for f in asyncio.as_completed(futures):
        res = await f
        if res is not None:
            diffs.append(res)

    return {
        'build_changeset': build_changeset,
        'git_build_changeset': await get_github_commit(build_changeset),
        'overall_cur': overall['cur'],
        'overall_prev': overall['prev'],
        'diffs': diffs,
    }
