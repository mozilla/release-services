# -*- coding: utf-8 -*-

import responses

from shipit_code_coverage.github import GitHubUtils


@responses.activate
def test_get_commit(MERCURIAL_COMMIT):
    responses.add(responses.GET, 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/{}'.format(MERCURIAL_COMMIT), body='{} foo bar'.format(MERCURIAL_COMMIT), status=200)  # noqa
    gu = GitHubUtils('', '', '')
    assert gu.get_commit(MERCURIAL_COMMIT) == MERCURIAL_COMMIT


@responses.activate
def test_get_mercurial(GITHUB_COMMIT):
    responses.add(responses.GET, 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/{}'.format(GITHUB_COMMIT), body='foo {} bar'.format(GITHUB_COMMIT), status=200)  # noqa
    gu = GitHubUtils('', '', '')
    assert gu.get_mercurial(GITHUB_COMMIT) == GITHUB_COMMIT
