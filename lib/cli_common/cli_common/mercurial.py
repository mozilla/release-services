# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import hglib

import cli_common.log

log = cli_common.log.get_logger(__name__)


def hg_run(cmd):
    '''
    Run a mercurial command without an hglib instance
    Useful for initial custom clones
    '''
    proc = hglib.util.popen([hglib.HGPATH] + cmd)
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError(cmd, proc.returncode, out, err)
    return out


def robust_checkout(repo_url, repo_dir, branch=b'tip', revision=None):
    '''
    Helper to clone Mozilla Central
    '''
    assert isinstance(branch, bytes)

    shared_dir = repo_dir + '-shared'
    cmd = hglib.util.cmdbuilder('robustcheckout',
                                repo_url,
                                repo_dir,
                                purge=True,
                                sharebase=shared_dir,
                                branch=branch)
    hg_run(cmd)

    hg = hglib.open(repo_dir)
    hg.update(rev=revision, clean=True)

    return hg


def batch_checkout(repo_url, repo_dir, revision=b'tip', batch_size=100000):
    '''
    Helper to clone a mercurial repository using several steps
    to minimize memory footprint and stay below 1Gb of RAM
    It's used on Heroku small dynos
    '''
    assert isinstance(revision, bytes)
    assert isinstance(batch_size, int)
    assert batch_size > 1

    log.info('Batch checkout', url=repo_url, dir=repo_dir)
    cmd = hglib.util.cmdbuilder('clone',
                                repo_url,
                                repo_dir,
                                noupdate=True,
                                stream=True)
    hg_run(cmd)
    log.info('Inital clone finished')

    repo = hglib.open(repo_dir)
    target = int(repo.identify(rev=revision, num=True).strip().decode('utf-8'))
    log.info('Target revision for incremental checkout', revision=target)

    steps = list(range(1, target, batch_size)) + [target]
    for rev in steps:
        log.info('Moving repo to revision', dir=repo_dir, rev=rev)
        repo.update(rev=rev)

    return repo
