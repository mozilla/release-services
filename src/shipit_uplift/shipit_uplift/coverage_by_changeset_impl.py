# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
import whatthepatch
from shipit_uplift.coverage import coverage_service, get_coverage_build


def generate(changeset):
    '''
    This function generates a report containing the coverage information of the diff
    introduced by a changeset.
    '''
    build_changeset, _ = get_coverage_build(changeset)

    r = requests.get('https://hg.mozilla.org/mozilla-central/raw-rev/%s' % changeset)
    patch = r.text

    diffs = []

    for diff in whatthepatch.parse_patch(patch):
        # Get old and new path, for files that have been renamed.
        new_path = diff.header.new_path[2:] if diff.header.new_path.startswith('b/') else diff.header.new_path

        # If the diff doesn't contain any changes, we skip it.
        if diff.changes is None:
            continue

        # Retrieve coverage of added lines.
        coverage = coverage_service.get_file_coverage(build_changeset, new_path)

        # If we don't have coverage for this file, we skip it.
        if coverage is None:
            continue

        changes = []
        for old_line, new_line, _ in diff.changes:
            if old_line is None and new_line is not None:
                # Added line.
                if new_line not in coverage or coverage[new_line] is None:
                    # We have no coverage information for this line (e.g. a definition, like
                    # a variable in a header file).
                    covered = '?'
                elif coverage[new_line] > 0:
                    covered = 'Y'
                else:
                    covered = 'N'
            else:
                # Unmodified or removed line.
                continue

            changes.append({
                'coverage': covered,
                'old_line': old_line,
                'new_line': new_line,
            })

        diffs.append({
            'name': new_path,
            'changes': changes,
        })

    return {
        'build_changeset': build_changeset,
        'diffs': diffs,
    }
