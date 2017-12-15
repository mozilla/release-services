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
    # If the file is not a source file, we can return early (as we already know
    # we have no coverage information for it).
    if not coverage_supported(path):
        return {}

    _, build_changeset, _ = get_coverage_build(changeset)

    coverage = coverage_service.get_file_coverage(build_changeset, path)

    return coverage if coverage is not None else {}
