# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.mark.parametrize('name, expected', [
    ('code-coverage/api', 'code_coverage_api'),
    ('static_analysis/api', 'static_analysis_api'),
    ])
def test_python_module_name(name, expected):
    import common_naming  # noqa
    assert common_naming.Project(name).python_module_name == expected
    assert common_naming.Project(name).flask_app_name == expected


@pytest.mark.parametrize('name, expected', [
    ('code-coverage/api', 'mozilla-release-code-coverage-api'),
    ('static_analysis/api', 'mozilla-release-static-analysis-api'),
    ])
def test_distribution_name(name, expected):
    import common_naming  # noqa
    assert common_naming.Project(name).python_distribution_name == expected
