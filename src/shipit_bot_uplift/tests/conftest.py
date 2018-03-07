# -*- coding: utf-8 -*-
import tempfile
import pytest
import os
import shutil
import hglib


@pytest.fixture(scope='session')
def repository():
    '''
    Create a test Mercurial repository
    '''
    from shipit_bot_uplift.mercurial import Repository

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
