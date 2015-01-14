# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_
from relengapi.lib import introspection


def test_get_blueprints():
    blueprints = introspection.get_blueprints()
    base_blueprint = [bp for bp in blueprints if bp.name == 'base'][0]
    eq_(base_blueprint.dist.project_name, 'relengapi')


def test_get_distributions():
    distributions = introspection.get_distributions()
    eq_(distributions['relengapi'].project_name, 'relengapi')


def test_metadata():
    distributions = introspection.get_distributions()
    meta = distributions['relengapi'].relengapi_metadata
    assert 'repository_of_record' in meta
