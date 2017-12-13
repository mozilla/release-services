# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from shipit_uplift.coverage import coverage_service, get_coverage_build, coverage_supported


def generate(changeset, path):
    '''
    This function generates a report containing the coverage information for a given file
    at a given revision.
    '''
    desc, build_changeset, overall = get_coverage_build(changeset)
    if any(text in desc for text in ['r=merge', 'a=merge']):
        raise Exception('Retrieving coverage for merge commits is not supported.')

    # If the file is not a source file, we skip it (as we already know
    # we have no coverage information for it).
    if not coverage_supported(path):
        return {
            'build_changeset': build_changeset,
            'coverage': {},
        }

    # Retrieve coverage of added lines.
    coverage = coverage_service.get_file_coverage(build_changeset, path)

    # If we don't have coverage for this file, we skip it.
    if coverage is None:
        return {
            'build_changeset': build_changeset,
            'coverage': {},
        }

    return {
        'build_changeset': build_changeset,
        'coverage': coverage,
    }
