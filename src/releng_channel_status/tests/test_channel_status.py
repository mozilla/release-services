# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def get_channel_status_model(templates):
    assert templates
    key = 'channel_status'
    _, context = templates[0]
    assert key in context
    assert context[key] is not None
    return context[key]


def test_model_updates_are_currently(client, templates, updates_are_currently_requests_mock):
    with updates_are_currently_requests_mock:
        client.get('/')
        model = get_channel_status_model(templates)
        assert model.rule is not None
        assert model.is_latest_build_update
        assert not model.is_throttled
        assert model.release is not None
        assert model.default_release is not None
        assert model.fallback_release is None


def test_model_updates_are_frozen(client, templates, updates_are_frozen_requests_mock):
    with updates_are_frozen_requests_mock:
        client.get('/')
        model = get_channel_status_model(templates)
        assert model.rule is not None
        assert not model.is_latest_build_update
        assert model.release is not None
        assert model.default_release is not None
        assert model.frozen_reason is not None


def test_model_updates_are_throttled(client, templates, updates_are_throttled_requests_mock):
    with updates_are_throttled_requests_mock:
        client.get('/')
        model = get_channel_status_model(templates)
        assert model.rule is not None
        assert model.background_rate < 100
        assert model.is_latest_build_update
        assert model.is_throttled
        assert model.release is not None
        assert model.fallback_release is not None


def test_model_bg_rate_zero(client, templates, updates_are_latest_bg_rate_zero_requests_mock):
    with updates_are_latest_bg_rate_zero_requests_mock:
        client.get('/')
        model = get_channel_status_model(templates)
        assert model.rule is not None
        assert model.background_rate == 0
        assert model.is_not_serving_latest_update_mapping
        assert model.release is not None
        assert model.fallback_release is not None
