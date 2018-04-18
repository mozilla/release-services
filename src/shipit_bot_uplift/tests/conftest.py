# -*- coding: utf-8 -*-
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import os

import pytest


@pytest.fixture
def mock_taskcluster_credentials():
    '''
    Work around "Exception: Missing taskcluster in /etc/hosts"
    '''
    os.environ['TASKCLUSTER_CLIENT_ID'] = 'fake_client_id'
    os.environ['TASKCLUSTER_ACCESS_TOKEN'] = 'fake_access_token'
