# -*- coding: utf-8 -*-

import responses

from shipit_code_coverage.github import GitHubUtils


@responses.activate
def test_get_commit(GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.get_commit(MERCURIAL_COMMIT) == GITHUB_COMMIT


@responses.activate
def test_get_mercurial(GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.get_mercurial(GITHUB_COMMIT) == MERCURIAL_COMMIT
