import cli_common.log


log = cli_common.log.get_logger(__name__)


class Platform:
    def __init__(self, name, locales, aliased_platforms):
        self._name = name
        self.locales = locales
        self.aliased_platforms = aliased_platforms
    
    @property
    def name(self):
        names = [self._name]
        if self.aliased_platforms:
            names.extend(self.aliased_platforms)
        return ', '.join(names)


class Release:
    def __init__(self, release):
        self._release = release
        self.alias_key = 'alias'

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
                platforms.append(Platform(platform, platform_value['locales'], aliased_platforms.get(platform)))
        return platforms


class ChannelStatus:
    def __init__(self, rule, user_platform, user_locale, update_mappings):
        self.rule = rule
        self.user_platform = user_platform
        self.user_locale = user_locale
        self.update_mappings = update_mappings
        self.release = None
        self.fallback_release = None        

    @property
    def is_latest_build_update(self):
        return self.rule['mapping'] in self.update_mappings

    @property
    def comment(self):
        return self.rule['comment']

    @property
    def is_throttled(self):
        return self.background_rate < 100

    @property
    def background_rate(self):
        return self.rule['backgroundRate']
