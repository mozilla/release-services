# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
import whatthepatch
from shipit_uplift.coverage import coverage_service, get_coverage_builds


def generate(changeset):
    '''
    This function generates a report containing the coverage information of the diff
    introduced by a changeset.
    '''
    previous_build_changeset, _, next_build_changeset, _ = get_coverage_builds(changeset)

    r = requests.get('https://hg.mozilla.org/mozilla-central/raw-rev/%s' % changeset)
    patch = r.text

    diffs = []

    for diff in whatthepatch.parse_patch(patch):
        # Get old and new path, for files that have been renamed.
        old_path = diff.header.old_path[2:] if diff.header.old_path.startswith('a/') else diff.header.old_path
        new_path = diff.header.new_path[2:] if diff.header.new_path.startswith('b/') else diff.header.new_path

        # If the diff doesn't contain any changes, we skip it.
        if diff.changes is None:
            continue

        # Retrieve coverage of removed and added lines.
        new_coverage = coverage_service.get_file_coverage(next_build_changeset, new_path)
        old_coverage = coverage_service.get_file_coverage(previous_build_changeset, old_path)

        # If we don't have coverage for this file, we skip it.
        if old_coverage is None and new_coverage is None:
            continue

        changes = []
        for old_line, new_line, _ in diff.changes:
            if old_line is not None and new_line is None:
                # Removed line.
                if old_line not in old_coverage or old_coverage[old_line] is None:
                    coverage = '?'
                elif old_coverage[old_line] > 0:
                    coverage = 'Y'
                else:
                    coverage = 'N'
            elif old_line is None and new_line is not None:
                # Added line.
                if new_line not in new_coverage or new_coverage[new_line] is None:
                    # We have no coverage information for this line (e.g. a definition, like
                    # a variable in a header file).
                    coverage = '?'
                elif new_coverage[new_line] > 0:
                    coverage = 'Y'
                else:
                    coverage = 'N'
            else:
                # Unmodified line.
                continue

            changes.append({
                'coverage': coverage,
                'old_line': old_line,
                'new_line': new_line,
            })

        diffs.append({
            'name': new_path,
            'changes': changes,
        })

    return {
        'build_changeset': next_build_changeset,
        'previous_build_changeset': previous_build_changeset,
        'diffs': diffs,
    }
