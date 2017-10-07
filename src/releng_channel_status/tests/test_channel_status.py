# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

RULES_GET_MAJOR_PRIORITY = 100


def test_get_default_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_get_by_alias(client):
    response = client.get('/firefox-nightly')
    assert response.status_code == 200


def test_get_by_product_channel(client):
    response = client.get('/firefox/nightly')
    assert response.status_code == 200


def test_get_frozen(client):
    response = client.get('/firefox-nightly-froozen')
    assert response.status_code == 200


def get_channel_status_model(templates):
    assert templates
    key = 'channel_status'
    _, context = templates[0]
    assert key in context
    assert context[key] is not None
    return context[key]


def test_model_updates_are_currently(client, templates):
    client.get('/')
    model = get_channel_status_model(templates)
    assert model.rule is not None
    assert model.is_latest_build_update
    assert not model.is_throttled
    assert model.release is None
    assert model.fallback_release is None


def test_model_updates_are_currently_get_by_alias(client, templates):
    client.get('/firefox-nightly')
    model = get_channel_status_model(templates)
    assert model.rule is not None
    assert model.is_latest_build_update
    assert not model.is_throttled
    assert model.release is None
    assert model.fallback_release is None


def test_model_updates_are_currently_get_by_product_channel(client, templates):
    client.get('/firefox/nightly')
    model = get_channel_status_model(templates)
    assert model.rule is not None
    assert model.rule['priority'] == RULES_GET_MAJOR_PRIORITY
    assert model.is_latest_build_update
    assert not model.is_throttled
    assert model.release is None
    assert model.fallback_release is None


def test_model_updates_are_frozen(client, templates):
    client.get('/firefox-nightly-froozen')
    model = get_channel_status_model(templates)
    assert model.rule is not None
    assert not model.is_latest_build_update
    assert model.release is not None


def test_model_updates_are_throttled(client, templates):
    client.get('/firefox-nightly-throttled')
    model = get_channel_status_model(templates)
    assert model.rule is not None
    assert model.rule['backgroundRate'] < 100
    assert model.rule['fallbackMapping'] is not None
    assert model.is_latest_build_update
    assert model.is_throttled
    assert model.release is not None
    assert model.fallback_release is not None
