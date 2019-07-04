# -*- coding: utf-8 -*-

import os
import shutil

from code_coverage_bot import hgmo


def copy_pushlog_database(remote, local):
    shutil.copyfile(os.path.join(remote, '.hg/pushlog2.db'),
                    os.path.join(local, '.hg/pushlog2.db'))


def add_file(hg, repo_dir, name, contents):
    path = os.path.join(repo_dir, name)

    with open(path, 'w') as f:
        f.write(contents)

    hg.add(files=[bytes(path, 'ascii')])


def commit(hg, diff_rev=None):
    commit_message = 'Commit {}'.format(hg.status())
    if diff_rev is not None:
        commit_message += 'Differential Revision: https://phabricator.services.mozilla.com/D{}'.format(diff_rev)

    i, revision = hg.commit(message=commit_message,
                            user='Moz Illa <milla@mozilla.org>')

    return str(revision, 'ascii')


def changesets(repo_dir, revision):
    with hgmo.HGMO(repo_dir) as hgmo_server:
        return hgmo_server.get_automation_relevance_changesets(revision)
