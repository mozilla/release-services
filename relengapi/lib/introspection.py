# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
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
            relengapi_metadata = _get_relengapi_metadata(dist)
            if relengapi_metadata:
                dist.relengapi_metadata = relengapi_metadata
            _distributions[dist.key] = dist

    if not _blueprints:
        _blueprints = []
        entry_points = (list(pkg_resources.iter_entry_points('relengapi_blueprints'))
                        + list(pkg_resources.iter_entry_points('relengapi.blueprints')))
        for ep in entry_points:
            bp = ep.load()
            # make sure we have only one copy of each Distribution
            bp.dist = _distributions[ep.dist.key]
            _blueprints.append(bp)


def _get_relengapi_metadata(dist):
    req = dist.as_requirement()
    try:
        setup_cfg = pkg_resources.resource_stream(req, 'setup.cfg')
    except Exception:
        return {}
    cfg = ConfigParser.RawConfigParser()
    cfg.readfp(setup_cfg)
    if not cfg.has_section('relengapi'):
        return {}

    return {o: cfg.get('relengapi', o) for o in cfg.options('relengapi')}


def get_blueprints():
    _fetch()
    return _blueprints


def get_distributions():
    _fetch()
    return _distributions
