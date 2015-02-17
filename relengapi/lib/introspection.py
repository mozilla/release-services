# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pkg_resources

_blueprints = None
_distributions = None


def _fetch():
    # get blueprints, dists, and so on from pkg_resources.
    #
    # We're careful to load all of the blueprints exactly once and before
    # registering any of them, as this ensures everything is imported before
    # any of the @bp.register-decorated methods are called
    global _blueprints
    global _distributions

    if not _distributions:
        _distributions = {}
        for dist in pkg_resources.WorkingSet():
            dist.relengapi_metadata = {}
            _distributions[dist.key] = dist

    if not _blueprints:
        _blueprints = []
        entry_points = (list(pkg_resources.iter_entry_points('relengapi_blueprints')) +
                        list(pkg_resources.iter_entry_points('relengapi.blueprints')))
        for ep in entry_points:
            bp = ep.load()
            # make sure we have only one copy of each Distribution
            bp.dist = _distributions[ep.dist.key]
            _blueprints.append(bp)

    # look for relengapi metadata for every dist containing a blueprint
    blueprint_dists = {bp.dist.key: bp.dist for bp in _blueprints}.values()
    for dist in blueprint_dists:
        ep = pkg_resources.get_entry_info(dist, 'relengapi.metadata', dist.key)
        if not ep:
            continue
        dist.relengapi_metadata = ep.load()


def get_blueprints():
    _fetch()
    return _blueprints


def get_distributions():
    _fetch()
    return _distributions
