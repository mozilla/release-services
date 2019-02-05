# -*- coding: utf-8 -*-
import os.path

import pytest

from pulselistener.mercurial import MercurialWorker


@pytest.mark.asyncio
async def test_push_to_try(PhabricatorMock, RepoMock):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    '''
    # Get initial tip commit in repo
    initial = RepoMock.tip()

    # The patched file should not exists at first
    repo_dir = RepoMock.root().decode('utf-8')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            ssh_user='john@doe.com',
            ssh_key='privateSSHkey',
            repo_url='http://mozilla-central',
            repo_dir=repo_dir,
        )
        worker.repo = RepoMock

        await worker.handle_diff({
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,
            'baseRevision': 'abcdef12345',
        })

    # The target should have content now
    assert os.path.exists(target)
    assert open(target).read() == 'First Line\nSecond Line\n'

    # Get tip commit in repo
    # It should be different from the initial one (patches have applied)
    tip = RepoMock.tip()
    assert tip.node != initial.node

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(worker.ssh_key_path)
    RepoMock.push.assert_called_with(
        dest=b'ssh://hg.mozilla.org/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )
