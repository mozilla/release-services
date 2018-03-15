# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from contextlib import contextmanager
import json
import os
import responses
import tempfile
import zipfile
import pytest


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


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
def MERCURIAL_COMMIT():
    return '40e8eb46609dcb8780764774ec550afff1eed3a5'


@pytest.fixture(scope='session')
def GITHUB_COMMIT():
    return 'f229b7e5d91eb70d23d3e31db7caff9d69a2ef04'


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
def mock_get_commit(MERCURIAL_COMMIT):
    responses.add(
        responses.GET,
        'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/{}'.format(MERCURIAL_COMMIT),
        body='{} 0d1e55d87931fe70ec1d007e886bcd58015ff770'.format(MERCURIAL_COMMIT),
        status=200)


@pytest.fixture(scope='session')
def mock_get_mercurial(GITHUB_COMMIT):
    responses.add(
        responses.GET,
        'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/{}'.format(GITHUB_COMMIT),
        body='876c7dd30586f9c6f9c99ef7444f2d73c7acfe7c {}'.format(GITHUB_COMMIT),
        status=200)
