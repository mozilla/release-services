# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import requests
import whatthepatch
from shipit_uplift.coverage import coverage_service, get_coverage_build, coverage_supported, get_github_commit


def generate(changeset):
    '''
    This function generates a report containing the coverage information of the diff
    introduced by a changeset.
    '''
    desc, build_changeset, overall = get_coverage_build(changeset)
    if any(text in desc for text in ['r=merge', 'a=merge']):
        raise Exception('Retrieving coverage for merge commits is not supported.')

    r = requests.get('https://hg.mozilla.org/mozilla-central/raw-rev/%s' % changeset)
    patch = r.text

    diffs = []

    def parse_diff(diff):
        # Get old and new path, for files that have been renamed.
        new_path = diff.header.new_path[2:] if diff.header.new_path.startswith('b/') else diff.header.new_path

        # If the diff doesn't contain any changes, we skip it.
        if diff.changes is None:
            return None

        # If the file is not a source file, we skip it (as we already know
        # we have no coverage information for it).
        if not coverage_supported(new_path):
            return None

        # Retrieve coverage of added lines.
        coverage = coverage_service.get_file_coverage(build_changeset, new_path)

        # If we don't have coverage for this file, we skip it.
        if coverage is None:
            return None

        changes = []
        for old_line, new_line, _ in diff.changes:
            # Only consider added lines.
            if old_line is not None or new_line is None:
                continue

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
                'line': new_line,
            })

        return {
          'name': new_path,
          'changes': changes,
        }

    def parse_diff_task(diff):
        return lambda: parse_diff(diff)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []

        for diff in whatthepatch.parse_patch(patch):
            futures.append(executor.submit(parse_diff_task(diff)))

        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                diffs.append(res)

    return {
        'build_changeset': build_changeset,
        'git_build_changeset': get_github_commit(build_changeset),
        'overall_cur': overall['cur'],
        'overall_prev': overall['prev'],
        'diffs': diffs,
    }
