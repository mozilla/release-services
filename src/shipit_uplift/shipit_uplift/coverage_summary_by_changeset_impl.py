# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
import whatthepatch
from shipit_uplift.coverage import coverage_service, get_coverage_builds


def generate(changeset):
    '''
    This function generates a summary of the overall coverage information for a changeset and
    of the diff introduced by a changeset.
    '''
    _, _, next_build_changeset, overall = get_coverage_builds(changeset, before=False)

    r = requests.get('https://hg.mozilla.org/mozilla-central/raw-rev/%s' % changeset)
    patch = r.text

    added = 0
    covered = 0

    for diff in whatthepatch.parse_patch(patch):
        new_path = diff.header.new_path[2:] if diff.header.new_path.startswith('b/') else diff.header.new_path

        # If the diff doesn't contain any changes, we skip it.
        if diff.changes is None:
            continue

        # Retrieve coverage of added lines.
        coverage = coverage_service.get_file_coverage(next_build_changeset, new_path)

        # If we don't have coverage for this file, we skip it.
        if coverage is None:
            continue

        for old_line, new_line, _ in diff.changes:
            # Only consider added lines.
            if old_line is not None or new_line is None:
                continue

            # Skip lines whose coverage info is missing.
            if new_line not in coverage or coverage[new_line] is None:
                continue

            added += 1

            if coverage[new_line] > 0:
                covered += 1

    return {
        'overall_cur': overall['cur'],
        'overall_prev': overall['prev'],
        'commit_added': added,
        'commit_covered': covered,
    }
