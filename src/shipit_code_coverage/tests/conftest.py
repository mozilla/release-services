# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import json
import os
import pytest


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(scope='session')
def TASK_NOT_FOUND():
    with open(os.path.join(FIXTURES_DIR, 'task_not_found.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def LATEST_LINUX():
    with open(os.path.join(FIXTURES_DIR, 'latest_linux.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def LINUX_TASK_ID():
    return 'MCIO1RWTRu2GhiE7_jILBw'


@pytest.fixture(scope='session')
def LINUX_TASK():
    with open(os.path.join(FIXTURES_DIR, 'linux_task.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def LINUX_TASK_STATUS():
    with open(os.path.join(FIXTURES_DIR, 'linux_task_status.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def LINUX_TASK_ARTIFACTS():
    with open(os.path.join(FIXTURES_DIR, 'linux_task_artifacts.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def LATEST_WIN():
    with open(os.path.join(FIXTURES_DIR, 'latest_win.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def WIN_TASK_ID():
    return 'PWnw3h-QQSiqxO83MDzKag'


@pytest.fixture(scope='session')
def GROUP_TASKS_1():
    with open(os.path.join(FIXTURES_DIR, 'task-group_1.json')) as f:
        return json.load(f)


@pytest.fixture(scope='session')
def GROUP_TASKS_2():
    with open(os.path.join(FIXTURES_DIR, 'task-group_2.json')) as f:
        return json.load(f)
