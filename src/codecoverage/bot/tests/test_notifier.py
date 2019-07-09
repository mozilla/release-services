# -*- coding: utf-8 -*-
import responses

from code_coverage_bot.notifier import notify_email
from code_coverage_bot.phabricator import PhabricatorUploader
from mercurial import add_file
from mercurial import changesets
from mercurial import commit
from mercurial import copy_pushlog_database


@responses.activate
def test_notification(mock_secrets, mock_phabricator, mock_notify, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n')
    commit(hg, 1)

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n')
    revision = commit(hg, 2)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    stack = changesets(local, revision)
    assert len(stack) == 2
    assert stack[0]['desc'] == "Commit [(b'A', b'file')]Differential Revision: https://phabricator.services.mozilla.com/D1"
    assert stack[1]['desc'] == "Commit [(b'M', b'file')]Differential Revision: https://phabricator.services.mozilla.com/D2"

    report = {
        'source_files': [{
            'name': 'file',
            'coverage': [None, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        }]
    }
    phab = PhabricatorUploader(local, revision)
    changesets_coverage = phab.generate(report, stack)

    assert changesets_coverage == {
        1: {
            'file': {
                'lines_added': 4,
                'lines_covered': 2,
                'coverage': 'NUCU'
            },
        },
        2: {
            'file': {
                'lines_added': 6,
                'lines_covered': 0,
                'coverage': 'NUCUUUUUUU',
            },
        },
    }

    mail = notify_email(revision, stack, changesets_coverage, 'testuser', 'testtoken')
    assert mail == "* [Commit [(b'M', b'file')]Differential Revision: https://phabricator.services.mozilla.com/D2](https://firefox-code-coverage.herokuapp.com/#/changeset/{}): 0 covered out of 6 added.\n".format(revision)  # noqa
