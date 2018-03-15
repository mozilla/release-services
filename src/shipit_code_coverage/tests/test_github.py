# -*- coding: utf-8 -*-

import responses

from shipit_code_coverage.github import GitHubUtils


@responses.activate
def test_get_commit(MERCURIAL_COMMIT, mock_get_commit):
    gu = GitHubUtils('', '', '')
    assert gu.get_commit(MERCURIAL_COMMIT) == MERCURIAL_COMMIT


@responses.activate
def test_get_mercurial(GITHUB_COMMIT, mock_get_mercurial):
    gu = GitHubUtils('', '', '')
    assert gu.get_mercurial(GITHUB_COMMIT) == GITHUB_COMMIT
