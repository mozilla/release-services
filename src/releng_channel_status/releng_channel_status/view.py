# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import cli_common.log
from flask import abort, current_app, render_template, request
from flask.views import MethodView
from .util import HttpRequestHelper
from .model import ChannelStatus, Release


log = cli_common.log.get_logger(__name__)


class BaseView(MethodView):
    @property
    def user_agent_platform(self):
        return request.user_agent.platform

    @property
    def user_agent_locale(self):
        locale = None
        if request.accept_languages:
            locale = request.accept_languages.best
        return locale


class ChannelStatusView(BaseView):
    def __init__(self, *args, **kwargs):
        super(ChannelStatusView, self).__init__(*args, **kwargs)
        self.http = HttpRequestHelper(current_app.config.get('BALROG_API_URL'))
        self.single_rule_endpoint = current_app.config.get('SINGLE_RULE_ENDPOINT')
        self.rules_endpoint = current_app.config.get('RULES_ENDPOINT')
        self.release_endpoint = current_app.config.get('RELEASE_ENDPOINT')
        self.update_mappings = current_app.config.get('UPDATE_MAPPINGS')

    def get(self, rule_alias, product, channel):
        rule = self._get_rule(rule_alias, product, channel)
        if not rule:
            abort(404)
        model = self._get_channel_status(rule)
        return render_template('channel_status.html', channel_status=model)

    def _get_rule(self, rule_alias=None, product=None, channel=None):
        rule = None
        if rule_alias:
            rule = self.http.get(
                self.single_rule_endpoint.format(alias=rule_alias))
        elif product and channel:
            rules_response = self.http.get(self.rules_endpoint, product=product)
            if rules_response['count'] > 0:
                rules = sorted([r for r in rules_response['rules'] if r['channel'] == channel],
                               key=lambda k: k.get('priority', 0), reverse=True)
                rule = next(iter(rules), None)
        return rule

    def _get_release(self, mapping):
        return self.http.get(self.release_endpoint.format(release=mapping))

    def _get_channel_status(self, rule):
        channel_status = ChannelStatus(rule, self.update_mappings)
        if channel_status.is_throttled:
            fallback_release = self._get_release(rule['fallbackMapping'])
            channel_status.fallback_release = Release(fallback_release, self.user_agent_platform, self.user_agent_locale)
        if not channel_status.is_latest_build_update or channel_status.is_throttled:
            release = self._get_release(rule['mapping'])
            channel_status.release = Release(release, self.user_agent_platform, self.user_agent_locale)
        return channel_status
