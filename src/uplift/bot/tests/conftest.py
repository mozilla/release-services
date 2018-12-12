# -*- coding: utf-8 -*-
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import os
import shutil
import tempfile

import hglib
import pytest


@pytest.fixture
def mock_taskcluster_credentials():
    '''
    Work around "Exception: Missing taskcluster in /etc/hosts"
    '''
    os.environ['TASKCLUSTER_CLIENT_ID'] = 'fake_client_id'
    os.environ['TASKCLUSTER_ACCESS_TOKEN'] = 'fake_access_token'


@pytest.fixture(scope='session')
def repository():
    '''
    Create a test Mercurial repository
    '''
    from uplift_bot.mercurial import Repository

    # New repo in a temp dir
    root = tempfile.mkdtemp(prefix='hg.')
    hglib.init(root)
    client = hglib.open(root)

    # Add a few dummy commits
    readme = os.path.join(root, 'README.md')
    for i in range(5):
        with open(readme, 'a') as f:
            f.write('edit #{}\n'.format(i))

        msg = 'commit #{}'.format(i)
        client.commit(
            addremove=True,
            message=msg,
            user='pytest',
        )

    # Use our high level client
    repo = Repository('http://dummy', root)
    repo.client = client  # no checkout
    yield repo

    # Cleanup after execution
    shutil.rmtree(root)
