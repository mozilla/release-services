# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def generate(data):
    '''
    This function generates a summary of the overall coverage information for a changeset and
    of the diff introduced by a changeset.
    '''
    commit_added = 0
    commit_covered = 0
    for diff in data['diffs']:
        for change in diff['changes']:
            if change['coverage'] == '?':
                # Don't consider this line, as we don't have info for it.
                continue

            commit_added += 1
            if change['coverage'] == 'Y':
                commit_covered += 1

    return {
        'build_changeset': data['build_changeset'],
        'overall_cur': data['overall_cur'],
        'overall_prev': data['overall_prev'],
        'commit_added': commit_added,
        'commit_covered': commit_covered,
    }
