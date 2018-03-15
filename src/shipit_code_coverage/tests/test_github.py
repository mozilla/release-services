# -*- coding: utf-8 -*-

import responses

from shipit_code_coverage.github import GitHubUtils


@responses.activate
def test_get_commit(GITHUB_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.get_commit(GITHUB_COMMIT) == GITHUB_COMMIT


@responses.activate
def test_get_mercurial(MERCURIAL_COMMIT):
    gu = GitHubUtils('', '', '')
    assert gu.get_mercurial(MERCURIAL_COMMIT) == MERCURIAL_COMMIT
