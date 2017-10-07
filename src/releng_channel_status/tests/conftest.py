# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import


import pytest
import responses
from releng_channel_status.flask import app
from os import path
from urllib.parse import urljoin
from templatecontext import captured_templates


CURRENTLY_UPDATE_RULE_JSON = 'currently_update_rule.json'
FROZEN_RULE_JSON = 'frozen_rule.json'
FROZEN_RELEASE_JSON = 'frozen_release.json'
PRODUCT_CHANNEL_RULES_JSON = 'product_channel_rules.json'
THROTTLED_RULE_JSON = 'throttled_rule.json'

config = {'BALROG_API_URL': 'https://aus-api.mozilla.org/api/v1/',
          'SINGLE_RULE_ENDPOINT': 'rules/{alias}',
          'RULES_ENDPOINT': 'rules',
          'RELEASE_ENDPOINT': 'releases/{release}',
          'DEFAULT_ALIAS': 'firefox-nightly',
          'UPDATE_MAPPINGS': ['Firefox-mozilla-central-nightly-latest']}


def create_responses_mock():
    resp = responses.RequestsMock(assert_all_requests_are_fired=False)
    resp.add(responses.GET, single_rule_endpoint(config['DEFAULT_ALIAS']),
             body=get_json('resources/mocks/{}'.format(CURRENTLY_UPDATE_RULE_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, single_rule_endpoint('firefox-nightly-froozen'),
             body=get_json('resources/mocks/{}'.format(FROZEN_RULE_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, release_endpoint('Firefox-nightly-frozen'),
             body=get_json('resources/mocks/{}'.format(FROZEN_RELEASE_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, rules_endpoint('firefox', 'nightly'),
             body=get_json('resources/mocks/{}'.format(PRODUCT_CHANNEL_RULES_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, single_rule_endpoint('firefox-nightly-throttled'),
             body=get_json('resources/mocks/{}'.format(THROTTLED_RULE_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, release_endpoint('Firefox-mozilla-central-nightly-latest'),
             body=get_json('resources/mocks/{}'.format(THROTTLED_RULE_JSON)),
             status=200,
             content_type='application/json')
    resp.add(responses.GET, release_endpoint('Firefox-55.0.3-build2'),
             body=get_json('resources/mocks/{}'.format(FROZEN_RELEASE_JSON)),
             status=200,
             content_type='application/json')
    return resp


def get_json(json_file):
    file_path = path.join(path.dirname(__file__), json_file)
    with open(file_path, 'r') as f:
        return f.read()


def single_rule_endpoint(alias):
    print(urljoin(
        config['BALROG_API_URL'], config['SINGLE_RULE_ENDPOINT'].format(alias=alias)))
    return urljoin(
        config['BALROG_API_URL'], config['SINGLE_RULE_ENDPOINT'].format(alias=alias))


def rules_endpoint(product, channel):
    return urljoin(
        config['BALROG_API_URL'], config['RULES_ENDPOINT']) + '?product={}&channel={}'.format(product, channel)


def release_endpoint(name):
    return urljoin(
        config['BALROG_API_URL'], config['RELEASE_ENDPOINT'].format(release=name))


@pytest.fixture
def templates():
    with captured_templates(app) as templ:
        yield templ


@pytest.fixture(scope='session')
def client():
    with app.test_client() as client:
        with create_responses_mock():
            yield client
