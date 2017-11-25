# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import cli_common.log


log = cli_common.log.get_logger(__name__)


class Platform:
    def __init__(self, name, locales, aliased_platforms):
        self._name = name
        self.locales = locales
        self.aliased_platforms = aliased_platforms
        self.is_user_platform = False

    @property
    def name(self):
        names = [self._name]
        if self.aliased_platforms:
            names.extend(self.aliased_platforms)
        return ', '.join(names)


class Release:
    def __init__(self, release, default_platform, default_locale, user_platform, user_locale):
        self._release = release
        self.alias_key = 'alias'
        self.user_platform = user_platform
        self.user_locale = user_locale
        self.default_platform = default_platform
        self.default_locale = default_locale

    def _get_aliased_platforms(self, release_platforms):
        aliased_platforms = {}
        for aliased_platform, platform_value in release_platforms.items():
            platform = platform_value.get(self.alias_key)
            if platform:
                if platform not in aliased_platforms:
                    aliased_platforms[platform] = set()
                aliased_platforms[platform].add(aliased_platform)
        return aliased_platforms

    @property
    def platforms(self):
        platforms = []
        release_platforms = self._release['platforms']
        aliased_platforms = self._get_aliased_platforms(release_platforms)
        for platform, platform_value in release_platforms.items():
            if self.alias_key not in platform_value:
                platform = Platform(
                    platform, platform_value['locales'], aliased_platforms.get(platform))
                platform.is_user_platform = self.user_platform.lower() in platform.name.lower()
                platforms.append(platform)
        return platforms

    @property
    def default_build_id(self):
        platform = next(iter([p for p in self.platforms if self.default_platform in p.name]), None)
        if platform:
            locale = next(iter([v for l, v in platform.locales.items() if self.default_locale == l]), None)
            return locale['buildID']
        return None

    @property
    def name(self):
        return self._release['name']


class ChannelStatus:
    def __init__(self, rule, update_mappings):
        self.rule = rule
        self.update_mappings = update_mappings
        self.release = None
        self.fallback_release = None

    @property
    def is_latest_build_update(self):
        return self.rule['mapping'] in self.update_mappings and self.background_rate != 0

    @property
    def comment(self):
        return self.rule['comment']

    @property
    def background_rate(self):
        return self.rule['backgroundRate']

    @property
    def is_throttled(self):
        return self.background_rate > 0 and self.background_rate < 100

    @property
    def product(self):
        return self.rule['product']

    @property
    def channel(self):
        return self.rule['channel']
