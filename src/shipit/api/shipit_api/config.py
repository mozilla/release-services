# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

PROJECT_NAME = 'shipit/api'
APP_NAME = 'shipit_api'

BREAKPOINT_VERSION = 60
SCOPE_PREFIX = 'project:releng:services/{}'.format(APP_NAME)

# When there is only one ESR release ESR_NEXT is set to '' and ESR_CURRENT is
# set to current ESR major version.  When we have 2 ESR releases, ESR_CURRENT
# should be using the major version of the older release, while ESR_NEXT should
# be using the major version of the release with greater version.
CURRENT_ESR = '60'
ESR_NEXT = ''
# Pre Firefox version
LATEST_FIREFOX_OLDER_VERSION = '3.6.28'
RELEASE_BRANCH = 'releases/mozilla-release'
BETA_BRANCH = 'releases/mozilla-beta'
ESR_BRANCH_PREFIX = 'releases/mozilla-esr'
# FIREFOX_NIGHTLY version is hard coded and requires a human to update it after
# the latest Nightly builds are available on CDNs after version bump (merge
# day).
# We could have used the in-tree version, but there can be race conditions,
# e.g. version bumped, but still no builds available.
FIREFOX_NIGHTLY = '65.0a1'
# Aurora has been replaced by Dev Edition, but some 3rd party applications may
# still rely on this value.
FIREFOX_AURORA = ''
