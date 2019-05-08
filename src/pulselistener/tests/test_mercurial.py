# -*- coding: utf-8 -*-
import json
import os.path
import urllib

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

    # The patched and config files should not exist at first
    repo_dir = RepoMock.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            ssh_user='john@doe.com',
            ssh_key='privateSSHkey',
            repo_url='http://mozilla-central',
            repo_dir=repo_dir,
            batch_size=100,
            publish_phabricator=False,
        )
        worker.repo = RepoMock

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,

            # Revision does not exist, will apply on tip
            'baseRevision': 'abcdef12345',
        }
        await worker.push_to_try('PHID-HMBT-deadbeef', diff)

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
    tip = RepoMock.tip()
    assert tip.node != initial.node

    # Check all commits messages
    assert [c.desc for c in RepoMock.log()] == [
        b'try_task_config for code-review\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A second commit message\nDifferential Diff: PHID-DIFF-test123',
        b'Bug XXX - A first commit message\nDifferential Diff: PHID-DIFF-xxxx',
        b'Readme'
    ]

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(worker.ssh_key_path)
    RepoMock.push.assert_called_with(
        dest=b'ssh://hg.mozilla.org/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )


@pytest.mark.asyncio
async def test_push_to_try_existing_rev(PhabricatorMock, RepoMock):
    '''
    Run mercurial worker on a single diff
    with a push to try server
    but applying on an existing revision
    '''
    repo_dir = RepoMock.root().decode('utf-8')

    def _readme(content):
        # Make a commit on README.md in the repo
        readme = os.path.join(repo_dir, 'README.md')
        with open(readme, 'a') as f:
            f.write(content)
        _, rev = RepoMock.commit(message=content.encode('utf-8'), user=b'test')
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
            ssh_user='john@doe.com',
            ssh_key='privateSSHkey',
            repo_url='http://mozilla-central',
            repo_dir=repo_dir,
            batch_size=100,
            publish_phabricator=False,
        )
        worker.repo = RepoMock

        diff = {
            'phid': 'PHID-DIFF-solo',
            'revisionPHID': 'PHID-DREV-solo',
            'id': 9876,

            # Revision does not exist, will apply on tip
            'baseRevision': base,
        }
        await worker.push_to_try('PHID-HMBT-deadbeef', diff)

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
    tip = RepoMock.tip()
    assert tip.node != base
    assert tip.desc == b'try_task_config for code-review\nDifferential Diff: PHID-DIFF-solo'

    # Check the push to try has been called
    # with tip commit
    ssh_conf = 'ssh -o StrictHostKeyChecking="no" -o User="john@doe.com" -o IdentityFile="{}"'.format(worker.ssh_key_path)
    RepoMock.push.assert_called_with(
        dest=b'ssh://hg.mozilla.org/try',
        force=True,
        rev=tip.node,
        ssh=ssh_conf.encode('utf-8'),
    )

    # Check the parent is the solo patch commit
    parents = RepoMock.parents(tip.node)
    assert len(parents) == 1
    parent = parents[0]
    assert parent.desc == b'A nice human readable commit message\nDifferential Diff: PHID-DIFF-solo'

    # Check the grand parent is the base, not extra
    great_parents = RepoMock.parents(parent.node)
    assert len(great_parents) == 1
    great_parent = great_parents[0]
    assert great_parent.node == base

    # Extra commit should not appear
    assert parent.node != extra
    assert great_parent.node != extra
    assert 'EXTRA' not in open(os.path.join(repo_dir, 'README.md')).read()


@pytest.mark.asyncio
async def test_treeherder_link(PhabricatorMock, RepoMock):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    '''
    # Get initial tip commit in repo
    initial = RepoMock.tip()

    # The patched and config files should not exist at first
    repo_dir = RepoMock.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            ssh_user='john@doe.com',
            ssh_key='privateSSHkey',
            repo_url='http://mozilla-central',
            repo_dir=repo_dir,
            batch_size=100,
            publish_phabricator=True,
        )
        worker.repo = RepoMock

        diff = {
            'phid': 'PHID-DIFF-test123',
            'revisionPHID': 'PHID-DREV-deadbeef',
            'id': 1234,
            'baseRevision': 'abcdef12345',
        }
        await worker.push_to_try('PHID-HMBT-somehash', diff)

        # Check the treeherder link was published
        assert api.mocks.calls[-1].request.url == 'http://phabricator.test/api/harbormaster.createartifact'
        assert api.mocks.calls[-1].response.status_code == 200

    # Tip should be updated
    tip = RepoMock.tip()
    assert tip.node != initial.node


@pytest.mark.asyncio
async def test_failure(PhabricatorMock, RepoMock):
    '''
    Run mercurial worker on a single diff
    and check the treeherder link publication as an artifact
    '''
    # Get initial tip commit in repo
    initial = RepoMock.tip()

    # The patched and config files should not exist at first
    repo_dir = RepoMock.root().decode('utf-8')
    config = os.path.join(repo_dir, 'try_task_config.json')
    target = os.path.join(repo_dir, 'test.txt')
    assert not os.path.exists(target)
    assert not os.path.exists(config)

    with PhabricatorMock as api:
        worker = MercurialWorker(
            api,
            ssh_user='john@doe.com',
            ssh_key='privateSSHkey',
            repo_url='http://mozilla-central',
            repo_dir=repo_dir,
            batch_size=100,
            publish_phabricator=True,
        )
        worker.repo = RepoMock

        diff = {
            # Missing revisionPHID will give an assertion error
            'phid': 'PHID-DIFF-test123',
            'id': 1234,
        }
        out = await worker.handle_build('PHID-somehash', diff)
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
        tip = RepoMock.tip()
        assert tip.node == initial.node
