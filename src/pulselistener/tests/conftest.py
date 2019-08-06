# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import collections
import json
import os.path
import urllib.parse
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock

import hglib
import pytest
import responses
from taskcluster.utils import stringDate

from pulselistener import taskcluster
from pulselistener.lib.mercurial import Repository
from pulselistener.lib.phabricator import PhabricatorActions

MOCK_DIR = os.path.join(os.path.dirname(__file__), 'mocks')


@pytest.fixture
def QueueMock():
    class Mock():
        def __init__(self):
            self.created_tasks = []
            self.groups = collections.defaultdict(list)

        def add_task_in_group(self, group_id, **task):
            self.groups[group_id].append(task)

        def status(self, task_id):
            for status in ['failed', 'completed', 'exception', 'pending']:
                if status in task_id:
                    return {
                        'status': {
                            'state': status,
                        }
                    }
            assert False

        def task(self, task_id):
            now = datetime.utcnow()

            if 'retry:' in task_id:
                retry = int(task_id[task_id.index('retry:')+6])
            else:
                retry = 3

            return {
                'created': stringDate(now),
                'deadline': stringDate(now + timedelta(hours=2)),
                'dependencies': [],
                'expires': stringDate(now + timedelta(hours=24)),
                'payload': {
                    'command': ['/bin/command'],
                    'env': {},
                    'image': 'alpine',
                    'maxRunTime': 3600,
                },
                'priority': 'lowest',
                'provisionerId': 'aws-provisioner-v1',
                'requires': 'all-completed',
                'retries': retry,
                'scopes': [],
                'routes': [
                    'index.{}.latest'.format(task_id),
                ],
                'taskGroupId': 'group-{}'.format(task_id),
                'workerType': 'niceWorker'
            }

        def createTask(self, task_id, payload):
            self.created_tasks.append((task_id, payload))

        def listTaskGroup(self, group_id, **kwargs):
            return {
                'taskGroupId': group_id,
                'tasks': [
                    {
                        'task': {
                            'metadata': {
                                'name': task.get('name', 'unknown'),
                            },
                            'payload': {
                                'env': task.get('env', {}),
                            }
                        }
                    }
                    for task in self.groups.get(group_id, [])
                ],
                'continuationToken': None,
            }

    return Mock()


@pytest.fixture
def NotifyMock():
    class Mock():
        def __init__(self):
            self.email_obj = {}

        def email(self, obj):
            self.email_obj.update(obj)

    return Mock()


@pytest.fixture
def HooksMock():
    class Mock():
        def __init__(self):
            self.obj = {}

        def triggerHook(self, group_id, hook_id, payload):
            self.obj = {
              'group_id': group_id,
              'hook_id': hook_id,
              'payload': payload,
            }
            return {
                'status': {
                    'taskId': 'fake_task_id',
                },
            }

    return Mock()


@pytest.fixture
def IndexMock():
    class Mock():
        def __init__(self):
            pass

        def findTask(self, path):
            assert path.startswith('project.releng.services.tasks.')
            failed = 'failed' in path
            return {
                'taskId': path[30:],
                'data': {
                    'state': failed and 'error' or 'done',
                    'error_code': failed and 'somethingBad' or None,
                    'monitoring_restart': (failed and 'restart' in path)
                }
            }

    return Mock()


@pytest.fixture
@contextmanager
def PhabricatorMock():
    '''
    Mock phabricator authentication process
    '''
    json_headers = {
        'Content-Type': 'application/json',
    }

    def _response(name):
        path = os.path.join(MOCK_DIR, 'phabricator', '{}.json'.format(name))
        assert os.path.exists(path), 'Missing mock {}'.format(path)
        return open(path).read()

    def _phab_params(request):
        # What a weird way to send parameters
        return json.loads(urllib.parse.parse_qs(request.body)['params'][0])

    def _diff_search(request):
        params = _phab_params(request)
        assert 'constraints' in params
        if 'revisionPHIDs' in params['constraints']:
            # Search from revision
            mock_name = 'search-{}'.format(params['constraints']['revisionPHIDs'][0])
        elif 'phids' in params['constraints']:
            # Search from diffs
            diffs = '-'.join(params['constraints']['phids'])
            mock_name = 'search-{}'.format(diffs)
        else:
            raise Exception('Unsupported diff mock {}'.format(params))
        return (200, json_headers, _response(mock_name))

    def _diff_raw(request):
        params = _phab_params(request)
        assert 'diffID' in params
        return (200, json_headers, _response('raw-{}'.format(params['diffID'])))

    def _edges(request):
        params = _phab_params(request)
        assert 'sourcePHIDs' in params
        return (200, json_headers, _response('edges-{}'.format(params['sourcePHIDs'][0])))

    def _create_artifact(request):
        params = _phab_params(request)
        assert 'buildTargetPHID' in params
        return (200, json_headers, _response('artifact-{}'.format(params['buildTargetPHID'])))

    def _send_message(request):
        params = _phab_params(request)
        assert 'buildTargetPHID' in params
        name = 'message-{}-{}'.format(params['buildTargetPHID'], params['type'])
        if params['unit']:
            name += '-unit'
        if params['lint']:
            name += '-lint'
        return (200, json_headers, _response(name))

    def _project_search(request):
        params = _phab_params(request)
        assert 'constraints' in params
        assert 'slugs' in params['constraints']
        return(200, json_headers, _response('projects'))

    def _revision_search(request):
        params = _phab_params(request)
        assert 'constraints' in params
        assert 'ids' in params['constraints']
        assert 'attachments' in params
        assert 'projects' in params['attachments']
        assert 'reviewers' in params['attachments']
        assert params['attachments']['projects']
        assert params['attachments']['reviewers']
        mock_name = 'revision-search-{}'.format(params['constraints']['ids'][0])
        return (200, json_headers, _response(mock_name))

    def _user_search(request):
        params = _phab_params(request)
        assert 'constraints' in params
        assert 'phids' in params['constraints']
        mock_name = 'user-search-{}'.format(params['constraints']['phids'][0])
        return (200, json_headers, _response(mock_name))

    with responses.RequestsMock(assert_all_requests_are_fired=False) as resp:

        resp.add(
            responses.POST,
            'http://phabricator.test/api/user.whoami',
            body=_response('auth'),
            content_type='application/json',
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/edge.search',
            callback=_edges,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/differential.diff.search',
            callback=_diff_search,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/differential.getrawdiff',
            callback=_diff_raw,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/harbormaster.createartifact',
            callback=_create_artifact,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/harbormaster.sendmessage',
            callback=_send_message,
        )

        resp.add(
            responses.POST,
            'http://phabricator.test/api/diffusion.repository.search',
            body=_response('repositories'),
            content_type='application/json',
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/project.search',
            callback=_project_search,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/differential.revision.search',
            callback=_revision_search,
        )

        resp.add_callback(
            responses.POST,
            'http://phabricator.test/api/user.search',
            callback=_user_search,
        )

        actions = PhabricatorActions(
            url='http://phabricator.test/api/',
            api_key='deadbeef',
        )
        actions.mocks = resp  # used to assert in tests on callbacks
        yield actions


def build_repository(tmpdir, name):
    '''
    Mock a local mercurial repo
    '''
    # Init empty repo
    repo_dir = str(tmpdir.mkdir(name).realpath())
    hglib.init(repo_dir)

    # Add default pull in Mercurial config
    hgrc = tmpdir.join(name, '.hg', 'hgrc')
    hgrc.write('[paths]\ndefault = {}'.format(repo_dir))

    # Open repo with config
    repo = hglib.open(repo_dir)

    # Commit a file on central
    readme = tmpdir.join(name, 'README.md')
    readme.write('Hello World')
    repo.add(str(readme.realpath()).encode('utf-8'))
    repo.branch(name=b'central', force=True)
    repo.commit(message=b'Readme', user='test')

    # Mock push to avoid reaching try server
    repo.push = MagicMock(return_value=True)

    return repo


@pytest.fixture
def mock_mc(tmpdir):
    '''
    Mock a Mozilla Central repository
    '''
    config = {
        'name': 'mozilla-central',
        'ssh_user': 'john@doe.com',
        'ssh_key': 'privateSSHkey',
        'url': 'http://mozilla-central',
        'try_url': 'http://mozilla-central/try',
        'batch_size': 100,
    }
    repo = Repository(config, tmpdir.realpath())
    repo.repo = build_repository(tmpdir, 'mozilla-central')
    repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))
    return repo


@pytest.fixture
def mock_nss(tmpdir):
    '''
    Mock an NSS repository
    '''
    config = {
        'name': 'nss',
        'ssh_user': 'john@doe.com',
        'ssh_key': 'privateSSHkey',
        'url': 'http://nss',
        'try_url': 'http://nss/try',
        'try_mode': 'syntax',
        'try_syntax': '-a -b XXX -c YYY',
        'batch_size': 100,
    }
    repo = Repository(config, tmpdir.realpath())
    repo.repo = build_repository(tmpdir, 'nss')
    repo.clone = MagicMock(side_effect=asyncio.coroutine(lambda: True))
    return repo


@pytest.fixture
def mock_taskcluster():
    '''
    Mock Tasklcuster authentication
    '''
    taskcluster.options = {
        'rootUrl': 'http://taskcluster.test'
    }

    responses.add(
        responses.GET,
        'https://queue.taskcluster.net/v1/task-group/aGroup/list',
        json={
            'taskGroupId': 'aGroup',
            'tasks': [],
        },
    )
