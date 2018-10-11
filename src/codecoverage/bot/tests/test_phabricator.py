# -*- coding: utf-8 -*-

import os
import shutil

import responses

from code_coverage_bot.phabricator import PhabricatorUploader


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


@responses.activate
def test_upload_simple(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    revision = commit(hg, 1)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file',
            'coverage': [None, 0, 1, 1, 1, 1, 0],
        }]
    })

    assert set(results.keys()) == set([1])
    assert set(results[1].keys()) == set(['file'])
    assert results[1]['file'] == 'NUCCCCU'


@responses.activate
def test_upload_file_with_no_coverage(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    revision = commit(hg, 1)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': []
    })

    assert set(results.keys()) == set([1])
    assert set(results[1].keys()) == set()


@responses.activate
def test_upload_one_commit_without_differential(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    revision = commit(hg)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file_one_commit',
            'coverage': [None, 0, 1, 1, 1, 1, 0],
        }]
    })

    assert set(results.keys()) == set()


@responses.activate
def test_upload_two_commits_two_files(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file1_commit1', '1\n2\n3\n4\n5\n6\n7\n')
    add_file(hg, local, 'file2_commit1', '1\n2\n3\n')
    revision = commit(hg, 1)

    add_file(hg, local, 'file3_commit2', '1\n2\n3\n4\n5\n')
    revision = commit(hg, 2)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file1_commit1',
            'coverage': [None, 0, 1, 1, 1, 1, 0],
        }, {
            'name': 'file2_commit1',
            'coverage': [1, 1, 0],
        }, {
            'name': 'file3_commit2',
            'coverage': [1, 1, 0, 1, None],
        }]
    })

    assert set(results.keys()) == set([1, 2])
    assert set(results[1].keys()) == set(['file1_commit1', 'file2_commit1'])
    assert set(results[2].keys()) == set(['file3_commit2'])
    assert results[1]['file1_commit1'] == 'NUCCCCU'
    assert results[1]['file2_commit1'] == 'CCU'
    assert results[2]['file3_commit2'] == 'CCUCN'


@responses.activate
def test_upload_changesets_overwriting(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    commit(hg, 1)

    add_file(hg, local, 'file', '1\n2\n3\n42\n5\n6\n7\n')
    revision = commit(hg, 2)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file',
            'coverage': [None, 0, 1, 1, 1, 1, 0],
        }]
    })

    assert set(results.keys()) == set([1, 2])
    assert set(results[1].keys()) == set(['file'])
    assert set(results[2].keys()) == set(['file'])
    assert results[1]['file'] == 'NUCXCCU'
    assert results[2]['file'] == 'NUCCCCU'


@responses.activate
def test_upload_changesets_displacing(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    commit(hg, 1)

    add_file(hg, local, 'file', '-1\n-2\n1\n2\n3\n4\n5\n6\n7\n8\n9\n')
    revision = commit(hg, 2)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file',
            'coverage': [0, 1, None, 0, 1, 1, 1, 1, 0, 1, 0],
        }]
    })

    assert set(results.keys()) == set([1, 2])
    assert set(results[1].keys()) == set(['file'])
    assert set(results[2].keys()) == set(['file'])
    assert results[1]['file'] == 'NUCCCCU'
    assert results[2]['file'] == 'UCNUCCCCUCU'


@responses.activate
def test_upload_changesets_reducing_size(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    commit(hg, 1)

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n')
    revision = commit(hg, 2)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file',
            'coverage': [None, 0, 1, 1, 1],
        }]
    })

    assert set(results.keys()) == set([1, 2])
    assert set(results[1].keys()) == set(['file'])
    assert set(results[2].keys()) == set(['file'])
    assert results[1]['file'] == 'NUCCCXX'
    assert results[2]['file'] == 'NUCCC'


@responses.activate
def test_upload_changesets_overwriting_one_commit_without_differential(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    commit(hg, 1)

    add_file(hg, local, 'file', '1\n2\n3\n42\n5\n6\n7\n')
    revision = commit(hg)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': [{
            'name': 'file',
            'coverage': [None, 0, 1, 1, 1, 1, 0],
        }]
    })

    assert set(results.keys()) == set([1])
    assert set(results[1].keys()) == set(['file'])
    assert results[1]['file'] == 'NUCXCCU'


@responses.activate
def test_removed_file(mock_secrets, mock_phabricator, fake_hg_repo):
    hg, local, remote = fake_hg_repo

    add_file(hg, local, 'file', '1\n2\n3\n4\n5\n6\n7\n')
    commit(hg, 1)

    hg.remove(files=[bytes(os.path.join(local, 'file'), 'ascii')])
    revision = commit(hg)

    hg.push(dest=bytes(remote, 'ascii'))

    copy_pushlog_database(remote, local)

    phabricator = PhabricatorUploader(local, revision)
    results = phabricator.generate({
        'source_files': []
    })

    assert set(results.keys()) == set([1])
    assert set(results[1].keys()) == set()
