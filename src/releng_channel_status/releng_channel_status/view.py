import cli_common.log
from backend_common.cache import cache
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
        if request.user_agent.language:
            ll = request.user_agent.language.split('-')
            if len(ll) > 1:
                locale = ll[1]
        return locale


class ChannelStatusView(BaseView):
    def __init__(self, *args, **kwargs):
        super(ChannelStatusView, self).__init__(*args, **kwargs)
        self.http = HttpRequestHelper(current_app.config.get('BALROG_API_URL'))
        self.single_rule_endpoint = current_app.config.get(
            'SINGLE_RULE_ENDPOINT')
        self.rules_endpoint = current_app.config.get('RULES_ENDPOINT')
        self.release_endpoint = current_app.config.get('RELEASE_ENDPOINT')
        self.update_mappings = current_app.config.get('UPDATE_MAPPINGS')

    # @cache.memoize()
    def get(self, rule_alias, product, channel):
        rule = self._get_rule(rule_alias, product, channel)
        if not rule:
            abort(404)
        return self._create_response(rule)

    def _get_rule(self, rule_alias=None, product=None, channel=None):
        rule = None
        if rule_alias:
            rule = self.http.get(
                self.single_rule_endpoint.format(alias=rule_alias))
        elif product and channel:
            rules = self.http.get(self.rules_endpoint, product=product)
            if rules['count'] > 0:
                rule = next(
                    (r for r in rules['rules']
                     if r['channel'] == channel), None)
        return rule

    def _get_release(self, mapping):
        return self.http.get(self.release_endpoint.format(release=mapping))

    def _create_response(self, rule):
        channel_status = ChannelStatus(rule, self.user_agent_platform, self.user_agent_locale, self.update_mappings)
        if channel_status.is_throttled:
            fallback_release = self._get_release(rule['fallbackMapping'])
            channel_status.fallback_release = Release(fallback_release)
        if not channel_status.is_latest_build_update:
            release = self._get_release(rule['mapping'])
            channel_status.release = Release(release)
        return render_template('channel_status.html', channel_status=channel_status)
