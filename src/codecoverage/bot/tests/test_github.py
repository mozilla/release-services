# -*- coding: utf-8 -*-

import responses

from code_coverage_bot.github import GitHubUtils


@responses.activate
def test_get_commit(GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.mercurial_to_git(MERCURIAL_COMMIT) == GITHUB_COMMIT


@responses.activate
def test_get_mercurial(GITHUB_COMMIT, MERCURIAL_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.git_to_mercurial(GITHUB_COMMIT) == MERCURIAL_COMMIT
