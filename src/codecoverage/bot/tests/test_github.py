# -*- coding: utf-8 -*-

import responses

from code_coverage_bot.github import GitHubUtils


@responses.activate
def test_get_commit(mock_taskcluster, GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('')
    assert gu.mercurial_to_git(MERCURIAL_COMMIT) == GITHUB_COMMIT


@responses.activate
def test_get_mercurial(mock_taskcluster, GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('')
    assert gu.git_to_mercurial(GITHUB_COMMIT) == MERCURIAL_COMMIT
