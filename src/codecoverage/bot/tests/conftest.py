# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager

import hglib
import pytest
import responses

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_file(path):
    with open(os.path.join(FIXTURES_DIR, path)) as f:
        return f.read()


def load_json(path):
    with open(os.path.join(FIXTURES_DIR, path)) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def TASK_NOT_FOUND():
    return load_json('task_not_found.json')


@pytest.fixture(scope='session')
def LATEST_LINUX():
    return load_json('latest_linux.json')


@pytest.fixture(scope='session')
def LINUX_TASK_ID():
    return 'MCIO1RWTRu2GhiE7_jILBw'


@pytest.fixture(scope='session')
def LINUX_TASK():
    return load_json('linux_task.json')


@pytest.fixture(scope='session')
def LINUX_TASK_STATUS():
    return load_json('linux_task_status.json')


@pytest.fixture(scope='session')
def LINUX_TASK_ARTIFACTS():
    return load_json('linux_task_artifacts.json')


@pytest.fixture(scope='session')
def LATEST_WIN():
    return load_json('latest_win.json')


@pytest.fixture(scope='session')
def WIN_TASK_ID():
    return 'PWnw3h-QQSiqxO83MDzKag'


@pytest.fixture(scope='session')
def GROUP_TASKS_1():
    return load_json('task-group_1.json')


@pytest.fixture(scope='session')
def GROUP_TASKS_2():
    return load_json('task-group_2.json')


@pytest.fixture(scope='session')
def LINUX_TEST_TASK_ARTIFACTS():
    return load_json('linux_test_task_artifacts.json')


@pytest.fixture(scope='session')
def TEST_TASK_FROM_GROUP():
    return load_json('test_task_from_group.json')


@pytest.fixture()
def MERCURIAL_COMMIT():
    hg_commit = '0d1e55d87931fe70ec1d007e886bcd58015ff770'

    responses.add(
        responses.GET,
        'https://mapper.mozilla-releng.net/gecko-dev/rev/hg/{}'.format(hg_commit),
        body='40e8eb46609dcb8780764774ec550afff1eed3a5 {}'.format(hg_commit),
        status=200)

    return hg_commit


@pytest.fixture()
def GITHUB_COMMIT():
    git_commit = '40e8eb46609dcb8780764774ec550afff1eed3a5'

    responses.add(
        responses.GET,
        'https://mapper.mozilla-releng.net/gecko-dev/rev/git/{}'.format(git_commit),
        body='{} 0d1e55d87931fe70ec1d007e886bcd58015ff770'.format(git_commit),
        status=200)

    return git_commit


@contextmanager
def generate_coverage_artifact(name):
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, name + '.zip')
        with zipfile.ZipFile(zip_path, 'w') as z:
            z.write(os.path.join(FIXTURES_DIR, name))
        yield zip_path


@pytest.fixture(scope='session')
def grcov_artifact():
    with generate_coverage_artifact('grcov.info') as f:
        yield f


@pytest.fixture(scope='session')
def jsvm_artifact():
    with generate_coverage_artifact('jsvm.info') as f:
        yield f


@pytest.fixture(scope='session')
def file1_covered_artifact():
    with generate_coverage_artifact('file1_covered.info') as f:
        yield f


@pytest.fixture(scope='session')
def file1_uncovered_artifact():
    with generate_coverage_artifact('file1_uncovered.info') as f:
        yield f


@pytest.fixture(scope='session')
def file2_covered_artifact():
    with generate_coverage_artifact('file2_covered.info') as f:
        yield f


@pytest.fixture(scope='session')
def file2_uncovered_artifact():
    with generate_coverage_artifact('file2_uncovered.info') as f:
        yield f


@pytest.fixture(scope='session')
def grcov_existing_file_artifact():
    with generate_coverage_artifact('grcov_existing_file.info') as f:
        yield f


@pytest.fixture(scope='session')
def grcov_uncovered_artifact():
    with generate_coverage_artifact('grcov_uncovered_file.info') as f:
        yield f


@pytest.fixture(scope='session')
def jsvm_uncovered_artifact():
    with generate_coverage_artifact('jsvm_uncovered_file.info') as f:
        yield f


@pytest.fixture(scope='session')
def grcov_uncovered_function_artifact():
    with generate_coverage_artifact('grcov_uncovered_function.info') as f:
        yield f


@pytest.fixture(scope='session')
def jsvm_uncovered_function_artifact():
    with generate_coverage_artifact('jsvm_uncovered_function.info') as f:
        yield f


@pytest.fixture(scope='session')
def mock_secrets():
    from code_coverage_bot.secrets import secrets
    secrets.update({
        'CODECOV_REPO': 'marco-c/gecko-dev',
        'CODECOV_ACCESS_TOKEN': 'XXX',
        'PHABRICATOR_URL': 'http://phabricator.test/api/',
        'PHABRICATOR_TOKEN': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    })


@pytest.fixture()
def codecov_commits():
    dir_path = os.path.join(FIXTURES_DIR, 'codecov_commits')
    for fname in os.listdir(dir_path):
        with open(os.path.join(dir_path, fname)) as f:
            data = json.load(f)
            status = data['meta']['status']

            responses.add(
                responses.GET,
                'https://codecov.io/api/gh/marco-c/gecko-dev/commit/{}'.format(fname[:-5]),
                json=data,
                status=status
            )


@pytest.fixture
def fake_hg_repo(tmpdir):
    tmp_path = tmpdir.strpath
    dest = os.path.join(tmp_path, 'repos')
    local = os.path.join(dest, 'local')
    remote = os.path.join(dest, 'remote')
    for d in [local, remote]:
        os.makedirs(d)
        hglib.init(d)

    os.environ['USER'] = 'app'
    hg = hglib.open(local)

    responses.add_passthru('http://localhost:8000')

    yield hg, local, remote

    hg.close()


@pytest.fixture
def fake_hg_repo_with_contents(fake_hg_repo):
    hg, local, remote = fake_hg_repo

    files = [
        {'name': 'mozglue/build/dummy.cpp',
         'size': 1},
        {'name': 'toolkit/components/osfile/osfile.jsm',
         'size': 2},
        {'name': 'js/src/jit/JIT.cpp',
         'size': 3},
        {'name': 'toolkit/components/osfile/osfile-win.jsm',
         'size': 4},
        {'name': 'js/src/jit/BitSet.cpp',
         'size': 5},
        {'name': 'code_coverage_bot/cli.py',
         'size': 6},
        {'name': 'file1.jsm',
         'size': 7},
        {'name': 'file2.jsm',
         'size': 8},
    ]

    for c in '?!':
        for f in files:
            fname = os.path.join(local, f['name'])
            parent = os.path.dirname(fname)
            if not os.path.exists(parent):
                os.makedirs(parent)
            with open(fname, 'w') as Out:
                Out.write(c * f['size'])
            hg.add(files=[bytes(fname, 'ascii')])
            hg.commit(message='Commit file {} with {} inside'.format(fname, c),
                      user='Moz Illa <milla@mozilla.org>')
            hg.push(dest=bytes(remote, 'ascii'))

    shutil.copyfile(os.path.join(remote, '.hg/pushlog2.db'),
                    os.path.join(local, '.hg/pushlog2.db'))

    return local


@pytest.fixture
def mock_phabricator():
    '''
    Mock phabricator authentication process
    '''
    def _response(name):
        path = os.path.join(FIXTURES_DIR, 'phabricator_{}.json'.format(name))
        assert os.path.exists(path)
        return open(path).read()

    responses.add(
        responses.POST,
        'http://phabricator.test/api/user.whoami',
        body=_response('auth'),
        content_type='application/json',
    )


@pytest.fixture
def fake_source_dir(tmpdir):
    tmpdir_path = tmpdir.strpath

    os.makedirs(os.path.join(tmpdir_path, 'code_coverage_bot'))

    with open(os.path.join(tmpdir_path, 'code_coverage_bot', 'cli.py'), 'w') as f:
        f.write('1\n2\n')

    return tmpdir_path
