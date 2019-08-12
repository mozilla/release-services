# -*- coding: utf-8 -*-
import asyncio
import json
import os.path

import pytest

from pulselistener.lib.bus import MessageBus
from pulselistener.lib.mercurial import MercurialWorker
from pulselistener.lib.phabricator import PhabricatorBuild
from pulselistener.lib.phabricator import PhabricatorBuildState

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
        self.stack = []
        self.state = PhabricatorBuildState.Public


@pytest.mark.asyncio
async def test_push_to_try(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    '''
    bus = MessageBus()
    bus.add_queue('phabricator')

    # Preload the build
    diff = {
        'phid': 'PHID-DIFF-test123',
        'revisionPHID': 'PHID-DREV-deadbeef',
        'id': 1234,

        # Revision does not exist, will apply on tip
        'baseRevision': 'abcdef12345',
    }
    build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    # Get initial tip commit in repo
    initial = mock_mc.repo.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.repo.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-mc': mock_mc},
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

    await bus.send('mercurial', build)
    assert bus.queues['mercurial'].qsize() == 1
    task = asyncio.create_task(worker.run())

    # Check the treeherder link was queued
    mode, out_build, details = await bus.receive('phabricator')
    tip = mock_mc.repo.tip()
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
    assert [c.desc for c in mock_mc.repo.log()] == [
        b'try_task_config for code-review\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A second commit message\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A first commit message\nDifferential Diff: PHID-DIFF-xxxx',
        b'Readme'
    ]

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(mock_mc.ssh_key_path)
    mock_mc.repo.push.assert_called_with(
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
    repo_dir = mock_mc.repo.root().decode('utf-8')

    def _readme(content):
        # Make a commit on README.md in the repo
        readme = os.path.join(repo_dir, 'README.md')
        with open(readme, 'a') as f:
            f.write(content)
        _, rev = mock_mc.repo.commit(message=content.encode('utf-8'), user=b'test')
        return rev

    # Make two commits, the first one is our base
    base = _readme('Local base for diffs')
    extra = _readme('EXTRA')

    # Preload the build
    diff = {
        'phid': 'PHID-DIFF-solo',
        'revisionPHID': 'PHID-DREV-solo',
        'id': 9876,

        # Revision does not exist, will apply on tip
        'baseRevision': base,
    }
    build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-deadbeef', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    # The patched and config files should not exist at first
    target = os.path.join(repo_dir, 'solo.txt')
    config = os.path.join(repo_dir, 'try_task_config.json')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-mc': mock_mc},
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

    await bus.send('mercurial', build)
    assert bus.queues['mercurial'].qsize() == 1
    task = asyncio.create_task(worker.run())

    # Check the treeherder link was queued
    mode, out_build, details = await bus.receive('phabricator')
    tip = mock_mc.repo.tip()
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
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(mock_mc.ssh_key_path)
    mock_mc.repo.push.assert_called_with(
        dest=b'http://mozilla-central/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )

    # Check the parent is the solo patch commit
    parents = mock_mc.repo.parents(tip.node)
    assert len(parents) == 1
    parent = parents[0]
    assert parent.desc == b'A nice human readable commit message\nDifferential Diff: PHID-DIFF-solo'

    # Check the grand parent is the base, not extra
    great_parents = mock_mc.repo.parents(parent.node)
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
    # Preload the build
    diff = {
        'phid': 'PHID-DIFF-test123',
        'revisionPHID': 'PHID-DREV-deadbeef',
        'id': 1234,
        'baseRevision': 'abcdef12345',
    }
    build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-HMBT-somehash', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    bus = MessageBus()
    bus.add_queue('phabricator')

    # Get initial tip commit in repo
    initial = mock_mc.repo.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.repo.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-mc': mock_mc},
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

    await bus.send('mercurial', build)
    assert bus.queues['mercurial'].qsize() == 1
    task = asyncio.create_task(worker.run())

    # Check the treeherder link was queued
    mode, out_build, details = await bus.receive('phabricator')
    tip = mock_mc.repo.tip()
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
    diff = {
        'phid': 'PHID-DIFF-test123',
        'id': 1234,
        'baseRevision': None,
        'revisionPHID': 'PHID-DREV-deadbeef'
    }
    build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-somehash', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    bus = MessageBus()
    bus.add_queue('phabricator')

    # Get initial tip commit in repo
    initial = mock_mc.repo.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.repo.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    # Raise an exception during the workflow to trigger a broken build
    def boom(*args):
        raise Exception('Boom')
    mock_mc.apply_build = boom

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-mc': mock_mc}
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

    await bus.send('mercurial', build)
    assert bus.queues['mercurial'].qsize() == 1
    task = asyncio.create_task(worker.run())

    # Check the unit result was published
    mode, out_build, details = await bus.receive('phabricator')
    assert mode == 'fail:general'
    assert out_build == build
    assert details['duration'] > 0
    assert details['message'] == 'Boom'
    task.cancel()

    # Clone should not be modified
    tip = mock_mc.repo.tip()
    assert tip.node == initial.node


@pytest.mark.asyncio
async def test_failure_mercurial(PhabricatorMock, mock_mc):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    Apply a bad mercurial patch to trigger a mercurial fail
    '''
    diff = {
        'revisionPHID': 'PHID-DREV-666',
        'baseRevision': 'missing',
        'phid': 'PHID-DIFF-666',
        'id': 666,
    }
    build = MockBuild(1234, 'PHID-REPO-mc', 5678, 'PHID-build-666', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    bus = MessageBus()
    bus.add_queue('phabricator')

    # Get initial tip commit in repo
    initial = mock_mc.repo.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_mc.repo.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-mc': mock_mc}
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

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
    tip = mock_mc.repo.tip()
    assert tip.node == initial.node


@pytest.mark.asyncio
async def test_push_to_try_nss(PhabricatorMock, mock_nss):
    '''
    Run mercurial worker on a single diff
    with a push to try server, but with NSS support (try syntax)
    '''
    diff = {
        'phid': 'PHID-DIFF-test123',
        'revisionPHID': 'PHID-DREV-deadbeef',
        'id': 1234,

        # Revision does not exist, will apply on tip
        'baseRevision': 'abcdef12345',
    }
    build = MockBuild(1234, 'PHID-REPO-nss', 5678, 'PHID-HMBT-deadbeef', diff)
    with PhabricatorMock as phab:
        phab.load_patches_stack(build)

    bus = MessageBus()
    bus.add_queue('phabricator')

    # Get initial tip commit in repo
    initial = mock_nss.repo.tip()

    # The patched and config files should not exist at first
    repo_dir = mock_nss.repo.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    worker = MercurialWorker(
        'mercurial',
        'phabricator',
        repositories={'PHID-REPO-nss': mock_nss}
    )
    worker.register(bus)
    assert len(worker.repositories) == 1

    await bus.send('mercurial', build)
    assert bus.queues['mercurial'].qsize() == 1
    task = asyncio.create_task(worker.run())

    # Check the treeherder link was queued
    mode, out_build, details = await bus.receive('phabricator')
    tip = mock_nss.repo.tip()
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
    assert [c.desc for c in mock_nss.repo.log()] == [
        b'try: -a -b XXX -c YYY',
        b'Bug XXX - A second commit message\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A first commit message\nDifferential Diff: PHID-DIFF-xxxx',
        b'Readme'
    ]

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(mock_nss.ssh_key_path)
    mock_nss.repo.push.assert_called_with(
        dest=b'http://nss/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )
