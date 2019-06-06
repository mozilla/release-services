# -*- coding: utf-8 -*-
import collections
import json
import os.path
import urllib

import pytest

from pulselistener.mercurial import MercurialWorker

MERCURIAL_FAILURE = '''WARNING: The code review bot failed to apply your patch.

```unable to find 'crash.txt' for patching
(use '--prefix' to apply patch relative to the current directory)
1 out of 1 hunks FAILED -- saving rejects to file crash.txt.rej
abort: patch failed to apply
```'''

MockBuild = collections.namedtuple('MockBuild', 'diff_id, repo_phid, revision_id, target_phid, diff')


@pytest.mark.asyncio
async def test_push_to_try(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    '''
    # Get initial tip commit in repo
    initial = mock_mc.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'mozilla-central',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://mozilla-central',
                    'try_url': 'http://mozilla-central/try',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=False,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,

            # Revision does not exist, will apply on tip
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
        await worker.handle_build(repo, build)

        # Check the treeherder link was NOT published
        assert api.mocks.calls[-1].request.url != 'http://phabricator.test/api/harbormaster.createartifact'

    # The target should have content now
    assert os.path.exists(target)
    assert open(target).read() == 'First Line\nSecond Line\n'

    # Check the try_task_config file
    assert os.path.exists(config)
    assert json.load(open(config)) == {
        'version': 2,
        'parameters': {
            'target_tasks_method': 'codereview',
            'optimize_target_tasks': True,
            'phabricator_diff': 'PHID-HMBT-deadbeef',
        }
    }

    # Get tip commit in repo
    # It should be different from the initial one (patches + config have applied)
    tip = mock_mc.tip()
    assert tip.node != initial.node

    # Check all commits messages
    assert [c.desc for c in mock_mc.log()] == [
        b'try_task_config for code-review\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A second commit message\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A first commit message\nDifferential Diff: PHID-DIFF-xxxx',
        b'Readme'
    ]

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(repo.ssh_key_path)
    mock_mc.push.assert_called_with(
        dest=b'http://mozilla-central/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )


@pytest.mark.asyncio
async def test_push_to_try_existing_rev(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    but applying on an existing revision
    '''
    repo_dir = mock_mc.root().decode('utf-8')

    def _readme(content):
        # Make a commit on README.md in the repo
        readme = os.path.join(repo_dir, 'README.md')
        with open(readme, 'a') as f:
            f.write(content)
        _, rev = mock_mc.commit(message=content.encode('utf-8'), user=b'test')
        return rev

    # Make two commits, the first one is our base
    base = _readme('Local base for diffs')
    extra = _readme('EXTRA')

    # The patched and config files should not exist at first
    target = os.path.join(repo_dir, 'solo.txt')
    config = os.path.join(repo_dir, 'try_task_config.json')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'mozilla-central',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://mozilla-central',
                    'try_url': 'http://mozilla-central/try',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=False,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc

        diff = {
            'phid': 'PHID-DIFF-solo',
            'revisionPHID': 'PHID-DREV-solo',
            'id': 9876,

            # Revision does not exist, will apply on tip
            'baseRevision': base,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
        await worker.handle_build(repo, build)

        # Check the treeherder link was NOT published
        assert api.mocks.calls[-1].request.url != 'http://phabricator.test/api/harbormaster.createartifact'

    # The target should have content now
    assert os.path.exists(target)
    assert open(target).read() == 'Solo PATCH\n'

    # Check the try_task_config file
    assert os.path.exists(config)
    assert json.load(open(config)) == {
        'version': 2,
        'parameters': {
            'target_tasks_method': 'codereview',
            'optimize_target_tasks': True,
            'phabricator_diff': 'PHID-HMBT-deadbeef',
        }
    }

    # Get tip commit in repo
    # It should be different from the initial one (patches and config have applied)
    tip = mock_mc.tip()
    assert tip.node != base
    assert tip.desc == b'try_task_config for code-review\nDifferential Diff: PHID-DIFF-solo'

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(repo.ssh_key_path)
    mock_mc.push.assert_called_with(
        dest=b'http://mozilla-central/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )

    # Check the parent is the solo patch commit
    parents = mock_mc.parents(tip.node)
    assert len(parents) == 1
    parent = parents[0]
    assert parent.desc == b'A nice human readable commit message\nDifferential Diff: PHID-DIFF-solo'

    # Check the grand parent is the base, not extra
    great_parents = mock_mc.parents(parent.node)
    assert len(great_parents) == 1
    great_parent = great_parents[0]
    assert great_parent.node == base

    # Extra commit should not appear
    assert parent.node != extra
    assert great_parent.node != extra
    assert 'EXTRA' not in open(os.path.join(repo_dir, 'README.md')).read()


@pytest.mark.asyncio
async def test_treeherder_link(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    '''
    # Get initial tip commit in repo
    initial = mock_mc.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'mozilla-central',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://mozilla-central',
                    'try_url': 'http://mozilla-central/try',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=True,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-somehash', diff)
        await worker.handle_build(repo, build)

        # Check the treeherder link was published
        assert api.mocks.calls[-1].request.url == 'http://phabricator.test/api/harbormaster.createartifact'
        assert api.mocks.calls[-1].response.status_code == 200

    # Tip should be updated
    tip = mock_mc.tip()
    assert tip.node != initial.node


@pytest.mark.asyncio
async def test_failure_general(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    Use a Python common exception to trigger a broken build
    '''
    # Get initial tip commit in repo
    initial = mock_mc.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'mozilla-central',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://mozilla-central',
                    'try_url': 'http://mozilla-central/try',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=True,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc

        diff = {
            # Missing revisionPHID will give an assertion error
            'phid': 'PHID-DIFF-test123',
            'id': 1234,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-somehash', diff)
        out = await worker.handle_build(repo, build)
        assert out is False

        # Check the unit result was published
        assert api.mocks.calls[-1].request.url == 'http://phabricator.test/api/harbormaster.sendmessage'
        params = json.loads(urllib.parse.parse_qs(api.mocks.calls[-1].request.body)['params'][0])
        assert params['unit'][0]['duration'] > 0
        del params['unit'][0]['duration']
        assert params == {
            'buildTargetPHID': 'PHID-somehash',
            'type': 'fail',
            'unit': [
                {
                    'name': 'general',
                    'result': 'broken',
                    'namespace': 'code-review',
                    'details': 'WARNING: An error occured in the code review bot.\n\n``````',
                    'format': 'remarkup',
                }
            ],
            'lint': [],
            '__conduit__': {'token': 'deadbeef'}
        }
        assert api.mocks.calls[-1].response.status_code == 200

        # Clone should not be modified
        tip = mock_mc.tip()
        assert tip.node == initial.node


@pytest.mark.asyncio
async def test_failure_mercurial(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    Apply a bad mercurial patch to trigger a mercurial fail
    '''
    # Get initial tip commit in repo
    initial = mock_mc.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'mozilla-central',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://mozilla-central',
                    'try_url': 'http://mozilla-central/try',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=True,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc

        diff = {
            'revisionPHID': 'PHID-DREV-666',
            'baseRevision': 'missing',
            'phid': 'PHID-DIFF-666',
            'id': 666,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-build-666', diff)
        out = await worker.handle_build(repo, build)
        assert out is False

        # Check the unit result was published
        assert api.mocks.calls[-1].request.url == 'http://phabricator.test/api/harbormaster.sendmessage'
        params = json.loads(urllib.parse.parse_qs(api.mocks.calls[-1].request.body)['params'][0])
        assert params['unit'][0]['duration'] > 0
        del params['unit'][0]['duration']
        assert params == {
            'buildTargetPHID': 'PHID-build-666',
            'type': 'fail',
            'unit': [
                {
                    'name': 'mercurial',
                    'result': 'fail',
                    'namespace': 'code-review',
                    'details': MERCURIAL_FAILURE,
                    'format': 'remarkup',
                }
            ],
            'lint': [],
            '__conduit__': {'token': 'deadbeef'}
        }
        assert api.mocks.calls[-1].response.status_code == 200

        # Clone should not be modified
        tip = mock_mc.tip()
        assert tip.node == initial.node


@pytest.mark.asyncio
async def test_push_to_try_nss(PhabricatorMock, mock_nss):
    '''
    Run mercurial worker on a single diff
    with a push to try server, but with NSS support (try syntax)
    '''
    # Get initial tip commit in repo
    initial = mock_nss.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_nss.root().decode('utf-8')
    config = os.path.join(repo_dir, '.try')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            repositories=[
                {
                    'name': 'nss',
                    'ssh_user': 'john@doe.com',
                    'ssh_key': 'privateSSHkey',
                    'url': 'http://nss',
                    'try_url': 'http://nss/try',
                    'try_mode': 'syntax',
                    'try_syntax': '-a -b XXX -c YYY',
                    'batch_size': 100,
                }
            ],
            publish_phabricator=False,
            cache_root=os.path.dirname(repo_dir),
        )
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-nss')
        assert repo is not None
        repo.repo = mock_nss

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,

            # Revision does not exist, will apply on tip
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-nss', 5678, 'PHID-HMBT-deadbeef', diff)
        await worker.handle_build(repo, build)

        # Check the treeherder link was NOT published
        assert api.mocks.calls[-1].request.url != 'http://phabricator.test/api/harbormaster.createartifact'

    # The target should have content now
    assert os.path.exists(target)
    assert open(target).read() == 'First Line\nSecond Line\n'

    # Get tip commit in repo
    # It should be different from the initial one (patches + config have applied)
    tip = mock_nss.tip()
    assert tip.node != initial.node

    # Check all commits messages
    assert [c.desc for c in mock_nss.log()] == [
        b'try: -a -b XXX -c YYY',
        b'Bug XXX - A second commit message\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A first commit message\nDifferential Diff: PHID-DIFF-xxxx',
        b'Readme'
    ]

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(repo.ssh_key_path)
    mock_nss.push.assert_called_with(
        dest=b'http://nss/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )
