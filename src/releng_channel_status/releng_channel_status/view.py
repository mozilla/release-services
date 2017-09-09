from backend_common.cache import cache
from flask import current_app, request
from flask.views import MethodView
from .util import HttpRequestHelper


class BaseView(MethodView):
    def get_user_agent_platform(self):
        return request.user_agent.platform

    def get_user_agent_locale(self):
        return request.user_agent.language


class ChannelStatusView(BaseView):
    def __init__(self, *args, **kwargs):
        super(ChannelStatusView, self).__init__(*args, **kwargs)
        self.http = HttpRequestHelper(current_app.config.get('BALROG_API_URL'))
        self.single_rule_endpoint = current_app.config.get(
            'SINGLE_RULE_ENDPOINT')
        self.rules_endpoint = current_app.config.get('RULES_ENDPOINT')
        self.release_endpoint = current_app.config.get('RELEASE_ENDPOINT')

    @cache.memoize()
    def get(self, rule_alias, product, channel):
        rule = self._get_rule(rule_alias, product, channel)
        if not rule:
            return 404, 'Rule not found'
        release = self._get_release(rule['mapping'])
        return self._create_response(release)

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
        release = self.http.get(self.release_endpoint.format(release=mapping))
        return release

    def _create_response(self, release):
        if not release:
            return 404, 'Release not found'
        return str(release)
