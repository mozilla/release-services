# -*- coding: utf-8 -*-

import responses

from shipit_code_coverage.github import GitHubUtils


@responses.activate
def test_get_commit(GITHUB_COMMIT, MERCURIAL_COMMIT):
    responses.add(
        responses.GET,
        'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/{}'.format(MERCURIAL_COMMIT),
        body='40e8eb46609dcb8780764774ec550afff1eed3a5 {}'.format(MERCURIAL_COMMIT),
        status=200)

    gu = GitHubUtils('', '', '')
    assert gu.get_commit(MERCURIAL_COMMIT) == GITHUB_COMMIT


@responses.activate
def test_get_mercurial(GITHUB_COMMIT, MERCURIAL_COMMIT):
    responses.add(
        responses.GET,
        'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/{}'.format(GITHUB_COMMIT),
        body='{} 0d1e55d87931fe70ec1d007e886bcd58015ff770'.format(GITHUB_COMMIT),
        status=200)

    gu = GitHubUtils('', '', '')
    assert gu.get_mercurial(GITHUB_COMMIT) == MERCURIAL_COMMIT
