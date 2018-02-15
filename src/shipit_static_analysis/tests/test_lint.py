# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def test_flake8_rules(tmpdir, mock_config):
    '''
    Check flake8 rule detection
    '''
    from shipit_static_analysis.lint import MozLintIssue

    # Write dummy 3rd party file
    repo = tmpdir.mkdir('repo')
    third_party = repo.join(mock_config.third_party)
    third_party.write('test/dummy')

    # Valid issue
    issue = MozLintIssue(str(repo), 'test.py', 1, 'error', 1, 'flake8', 'Dummy test', 'dummy rule')
    assert not issue.is_disabled_rule()
    assert issue.is_publishable()

    # 3rd party
    issue = MozLintIssue(str(repo), 'test/dummy/XXX.py', 1, 'error', 1, 'flake8', 'Dummy test', 'dummy rule')
    assert not issue.is_disabled_rule()
    assert issue.is_third_party()
    assert not issue.is_publishable()

    # Flake8 bad quotes
    issue = MozLintIssue(str(repo), 'test.py', 1, 'error', 1, 'flake8', 'Remove bad quotes or whatever.', 'Q000')
    assert issue.is_disabled_rule()
    assert not issue.is_publishable()
