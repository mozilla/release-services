# -*- coding: utf-8 -*-
import asyncio
import json
import os.path
from unittest.mock import MagicMock

import pytest

from pulselistener.lib.bus import MessageBus
from pulselistener.mercurial import MercurialWorker
from pulselistener.phabricator import PhabricatorBuild

MERCURIAL_FAILURE = '''unable to find 'crash.txt' for patching
(use '--prefix' to apply patch relative to the current directory)
1 out of 1 hunks FAILED -- saving rejects to file crash.txt.rej
abort: patch failed to apply
'''


class MockBuild(PhabricatorBuild):
    def __init__(self, diff_id, repo_phid, revision_id, target_phid, diff):
        self.diff_id = diff_id
        self.repo_phid = repo_phid
        self.revision_id = revision_id
        self.target_phid = target_phid
        self.diff = diff


@pytest.mark.asyncio
async def test_push_to_try(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    '''
    bus = MessageBus()
    bus.add_queue('phabricator')

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
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,

            # Revision does not exist, will apply on tip
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the treeherder link was queued
        mode, out_build, details = await bus.receive('phabricator')
        tip = mock_mc.tip()
        assert mode == 'success'
        assert out_build == build
        assert details['treeherder_url'] == 'https://treeherder.mozilla.org/#/jobs?repo=try&revision={}'.format(tip.node.decode('utf-8'))
        task.cancel()

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
    bus = MessageBus()
    bus.add_queue('phabricator')
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
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            'phid': 'PHID-DIFF-solo',
            'revisionPHID': 'PHID-DREV-solo',
            'id': 9876,

            # Revision does not exist, will apply on tip
            'baseRevision': base,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the treeherder link was queued
        mode, out_build, details = await bus.receive('phabricator')
        tip = mock_mc.tip()
        assert mode == 'success'
        assert out_build == build
        assert details['treeherder_url'] == 'https://treeherder.mozilla.org/#/jobs?repo=try&revision={}'.format(tip.node.decode('utf-8'))
        task.cancel()

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
    bus = MessageBus()
    bus.add_queue('phabricator')

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
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-somehash', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the treeherder link was queued
        mode, out_build, details = await bus.receive('phabricator')
        tip = mock_mc.tip()
        assert mode == 'success'
        assert out_build == build
        assert details['treeherder_url'] == 'https://treeherder.mozilla.org/#/jobs?repo=try&revision={}'.format(tip.node.decode('utf-8'))
        task.cancel()

    # Tip should be updated
    assert tip.node != initial.node


@pytest.mark.asyncio
async def test_failure_general(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    Use a Python common exception to trigger a broken build
    '''
    bus = MessageBus()
    bus.add_queue('phabricator')

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
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            # Missing revisionPHID will give an assertion error
            'phid': 'PHID-DIFF-test123',
            'id': 1234,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-somehash', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the unit result was published
        mode, out_build, details = await bus.receive('phabricator')
        assert mode == 'fail:general'
        assert out_build == build
        assert details['duration'] > 0
        assert details['message'] == ''
        task.cancel()

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
    bus = MessageBus()
    bus.add_queue('phabricator')

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
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-mc')
        assert repo is not None
        repo.repo = mock_mc
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            'revisionPHID': 'PHID-DREV-666',
            'baseRevision': 'missing',
            'phid': 'PHID-DIFF-666',
            'id': 666,
        }
        build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-build-666', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the treeherder link was queued
        mode, out_build, details = await bus.receive('phabricator')
        assert mode == 'fail:mercurial'
        assert out_build == build
        assert details['duration'] > 0
        assert details['message'] == MERCURIAL_FAILURE
        task.cancel()

        # Clone should not be modified
        tip = mock_mc.tip()
        assert tip.node == initial.node


@pytest.mark.asyncio
async def test_push_to_try_nss(PhabricatorMock, mock_nss):
    '''
    Run mercurial worker on a single diff
    with a push to try server, but with NSS support (try syntax)
    '''
    bus = MessageBus()
    bus.add_queue('phabricator')

    # Get initial tip commit in repo
    initial = mock_nss.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_nss.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            'mercurial',
            'phabricator',
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
            cache_root=os.path.dirname(repo_dir),
        )
        worker.register(bus)
        assert len(worker.repositories) == 1
        repo = worker.repositories.get('PHID-REPO-nss')
        assert repo is not None
        repo.repo = mock_nss
        repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,

            # Revision does not exist, will apply on tip
            'baseRevision': 'abcdef12345',
        }
        build = MockBuild(1234, 'PHID-REPO-nss', 5678, 'PHID-HMBT-deadbeef', diff)
        await bus.send('mercurial', build)
        assert bus.queues['mercurial'].qsize() == 1
        task = asyncio.create_task(worker.run())

        # Check the treeherder link was queued
        mode, out_build, details = await bus.receive('phabricator')
        tip = mock_nss.tip()
        assert mode == 'success'
        assert out_build == build
        assert details['treeherder_url'] == 'https://treeherder.mozilla.org/#/jobs?repo=try&revision={}'.format(tip.node.decode('utf-8'))
        task.cancel()

    # The target should have content now
    assert os.path.exists(target)
    assert open(target).read() == 'First Line\nSecond Line\n'

    # The config should have content now
    assert os.path.exists(config)
    assert json.load(open(config)) == {
        'version': 2,
        'parameters': {
            'code-review': {
                'phabricator-build-target': 'PHID-HMBT-deadbeef',
            }
        },
    }

    # Get tip commit in repo
    # It should be different from the initial one (patches + config have applied)
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
