# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import enum
import functools
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import typing
import urllib.parse

import aiohttp
import arrow
import click
import mozilla_version.gecko
import mypy_extensions
import sqlalchemy
import sqlalchemy.orm

import cli_common.command
import cli_common.log
import cli_common.utils
import shipit_api.config
import shipit_api.models

logger = cli_common.log.get_logger(__name__)


@enum.unique
class Product(enum.Enum):
    DEVEDITION = 'devedition'
    FIREFOX = 'firefox'
    FENNEC = 'fennec'
    THUNDERBIRD = 'thunderbird'


@enum.unique
class ProductCategory(enum.Enum):
    MAJOR = 'major'
    DEVELOPMENT = 'dev'
    STABILITY = 'stability'
    ESR = 'esr'


File = str
ReleaseDetails = mypy_extensions.TypedDict('ReleaseDetails', {
    'category': str,
    'product': str,
    'build_number': int,
    'description': typing.Optional[str],
    'is_security_driven': bool,
    'version': str,
    'date': str,
})
Releases = mypy_extensions.TypedDict('Releases', {
  'releases': typing.Dict[str, ReleaseDetails],
})
L10n = str
ReleaseL10n = mypy_extensions.TypedDict('ReleaseL10n', {
    'platforms': typing.List[str],
    'revision': str,
})
ReleaseL10ns = typing.Dict[L10n, ReleaseL10n]
ReleasesHistory = typing.Dict[str, str]
PrimaryBuildDetails = mypy_extensions.TypedDict('PrimaryBuildDetails', {
    'filesize': float,
})
PrimaryBuild = mypy_extensions.TypedDict('PrimaryBuild', {
    'Linux': PrimaryBuildDetails,
    'OS X': PrimaryBuildDetails,
    'Windows': PrimaryBuildDetails,
})
PrimaryBuilds = typing.Dict[str, typing.Dict[str, PrimaryBuild]]
FirefoxVersions = mypy_extensions.TypedDict('FirefoxVersions', {
    'FIREFOX_NIGHTLY': str,
    'FIREFOX_AURORA': str,
    'FIREFOX_ESR': str,
    'FIREFOX_ESR_NEXT': str,
    'LATEST_FIREFOX_DEVEL_VERSION': str,
    'FIREFOX_DEVEDITION': str,
    'LATEST_FIREFOX_OLDER_VERSION': str,
    'LATEST_FIREFOX_RELEASED_DEVEL_VERSION': str,
    'LATEST_FIREFOX_VERSION': str,
})
L10nChangeset = mypy_extensions.TypedDict('L10nChangeset', {
    'changeset': str,
})
L10n = mypy_extensions.TypedDict('L10n', {
    'locales': typing.Dict[str, L10nChangeset],
    'submittedAt': str,
    'shippedAt': str,
    'name': str,
})
Language = mypy_extensions.TypedDict('Language', {
    'English': str,
    'native': str,
})
Languages = typing.Dict[str, Language]
MobileDetailsBuildLocale = mypy_extensions.TypedDict('MobileDetailsBuildLocale', {
    'code': str,
    'english': str,
    'native': str,
})
MobileDetailsBuildDownload = mypy_extensions.TypedDict('MobileDetailsBuildDownload', {
    'android': str,
})
MobileDetailsBuild = mypy_extensions.TypedDict('MobileDetailsBuild', {
    'locale': MobileDetailsBuildLocale,
    'download': MobileDetailsBuildDownload,
})
MobileDetails = mypy_extensions.TypedDict('MobileDetails', {
    'nightly_version': str,
    'alpha_version': str,
    'beta_version': str,
    'version': str,
    'ios_beta_version': str,
    'ios_version': str,
    'builds': typing.List[MobileDetailsBuild],
    'beta_builds': typing.List[MobileDetailsBuild],
    'alpha_builds': typing.List[MobileDetailsBuild],
})
MobileVersions = mypy_extensions.TypedDict('MobileVersions', {
    'nightly_version': str,
    'alpha_version': str,
    'beta_version': str,
    'version': str,
    'ios_beta_version': str,
    'ios_version': str,
})
Region = typing.Dict[str, str]
ThunderbirdVersions = mypy_extensions.TypedDict('ThunderbirdVersions', {
    'LATEST_THUNDERBIRD_VERSION': str,
    'LATEST_THUNDERBIRD_ALPHA_VERSION': str,
    'LATEST_THUNDERBIRD_DEVEL_VERSION': str,
    'LATEST_THUNDERBIRD_NIGHTLY_VERSION': str,
})
IndexListing = str
ProductDetails = typing.Dict[File, typing.Union[
    Releases,
    ReleasesHistory,
    PrimaryBuilds,
    FirefoxVersions,
    MobileVersions,
    MobileDetails,
    Region,
    L10n,
    Languages,
    ThunderbirdVersions,
    IndexListing
]]
Products = typing.List[Product]

A = typing.TypeVar('A')
B = typing.TypeVar('B')


def with_default(a: typing.Optional[A],
                 func: typing.Callable[[A], B],
                 default: B,
                 ) -> B:
    if a is None:
        return default
    return func(a)


def to_isoformat(d: datetime.datetime) -> str:
    return arrow.get(d).isoformat()


def to_format(d: datetime.datetime, format: str) -> str:
    return arrow.get(d).format(format)


def get_product_mozilla_version(product: Product,
                                version: str,
                                ) -> typing.Optional[mozilla_version.gecko.GeckoVersion]:
    klass = {
        Product.DEVEDITION: mozilla_version.gecko.DeveditionVersion,
        Product.FIREFOX: mozilla_version.gecko.FirefoxVersion,
        Product.FENNEC: mozilla_version.gecko.FennecVersion,
        Product.THUNDERBIRD: mozilla_version.gecko.ThunderbirdVersion,
    }.get(product)

    if klass:
        return klass.parse(version)
    return None


def create_index_listing_html(folder: pathlib.Path,
                              items: typing.Set[pathlib.Path]
                              ) -> str:

    folder = '/' / folder  # noqa : T484 Unsupported left operand type for / ("str")
    with io.StringIO() as html:

        def write(x):
            return html.write(f'{x}{os.linesep}')

        write(f'<!doctype html>')
        write(f'<html>')
        write(f'  <head>')
        write(f'    <title>Index of {folder}</title>')
        write(f'  </head>')
        write(f'  <body>')
        write(f'    <h1>Index of {folder}</h1>')
        write(f'    <ul>')
        if folder != folder.parent:
            write(f'      <li><a href="{folder.parent}"> Parent Directory</a></li>')
        for item in sorted(items):
            is_dir = item.suffix not in ['.json', '.html']
            itemStr = is_dir and f'{item.name}/' or f'{item.name}'
            write(f'      <li><a href="{itemStr}"> {itemStr}</a></li>')
        write(f'    </ul>')
        write(f'  </body>')
        write(f'</html>')

        return html.getvalue()


def create_index_listing(product_details: ProductDetails) -> ProductDetails:
    new_product_details: ProductDetails = dict()
    folders: typing.Dict[pathlib.Path, typing.List[pathlib.Path]] = dict()

    for file_, content in product_details.items():
        new_product_details[file_] = content

        path = pathlib.Path(file_)
        for folder in list(path.parents):
            folders.setdefault(folder, [])
            folders[folder].append(path)
            path = folder

    for folder, items in folders.items():
        new_product_details[str(folder / 'index.html')] = create_index_listing_html(folder, set(items))

    return new_product_details


async def fetch_l10n_data(
        session: aiohttp.ClientSession,
        release: shipit_api.models.Release,
        git_branch: str,
        ) -> typing.Tuple[shipit_api.models.Release, typing.Optional[ReleaseL10ns]]:

    url_file = {
        Product.FIREFOX: 'browser/locales/l10n-changesets.json',
        Product.DEVEDITION: 'browser/locales/l10n-changesets.json',
        Product.FENNEC: 'mobile/locales/l10n-changesets.json',
        Product.THUNDERBIRD: 'mail/locales/l10n-changesets.json',
    }[Product(release.product)]
    url = f'{shipit_api.config.HG_PREFIX}/{release.branch}/raw-file/{release.revision}/{url_file}'

    # some thunderbird on the betas don't have l10n in the repository
    if Product(release.product) is Product.THUNDERBIRD and \
       release.branch == 'releases/comm-beta' and \
       release.revision in [
            '3e01e0dc6943',
            '481fea2011e6',
            '85cb8f907b18',
            '92950b2fd2dc',
            'c614b6e7cf58',
            'e277e3f0ab13',
            'efd290b55a35',
            'f87ba53e04ff',
            ]:
        return (release, None)

    cache_dir = shipit_api.config.PRODUCT_DETAILS_CACHE_DIR / 'fetch_l10n_data'
    os.makedirs(cache_dir, exist_ok=True)

    cache = cache_dir / hashlib.sha256(url.encode('utf-8')).hexdigest()
    if cache.exists():
        logger.debug(f'Cache hit for {url}')
        with cache.open() as f:
            changesets = json.load(f)
    else:
        logger.debug(f'Fetching {url}')
        changesets = dict()
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                logger.debug(f'Fetched {url}')
                changesets = await response.json()
                with cache.open('w+') as f:
                    f.write(json.dumps(changesets))
        except Exception as e:
            logger.exception(e)
            if git_branch == 'production':
                raise

    return (release, changesets)


def get_old_product_details(directory: str) -> ProductDetails:

    if not os.path.isdir(directory):
        return dict()

    data = dict()
    for root_, _, files in os.walk(directory):
        root = pathlib.Path(root_)
        for file__ in files:
            if not file__.endswith('.json'):
                continue
            file_ = root / file__
            with file_.open() as f:
                data[str(file_.relative_to(directory))] = json.load(f)

    return data


def get_releases_from_db(db_session: sqlalchemy.orm.Session,
                         breakpoint_version: int,
                         ) -> typing.List[shipit_api.models.Release]:
    '''
     SELECT *
     FROM shipit_api_releases as r
     WHERE cast(split_part(r.version, '.', 1) as int) > 20;
    '''
    Release = shipit_api.models.Release
    query = db_session.query(Release)
    # Using cast and split_part is postgresql specific
    query = query.filter(Release.status == 'shipped')
    query = query.filter(sqlalchemy.cast(sqlalchemy.func.split_part(Release.version, '.', 1),
                                         sqlalchemy.Integer) >= breakpoint_version)
    return query.all()


def get_product_categories(product: Product,
                           version: str,
                           ) -> typing.List[ProductCategory]:

    # typically, these are dot releases that are considered major
    SPECIAL_FIREFOX_MAJORS = ['14.0.1']
    SPECIAL_THUNDERBIRD_MAJORS = ['14.0.1', '38.0.1']

    def patternize_versions(versions):
        if not versions:
            return ''
        return '|' + '|'.join([v.replace(r'.', r'\.') for v in versions])

    categories = []
    categories_mapping: typing.List[typing.Tuple[ProductCategory, str]] = []

    if product is Product.THUNDERBIRD:
        special_majors = patternize_versions(SPECIAL_THUNDERBIRD_MAJORS)
    else:
        special_majors = patternize_versions(SPECIAL_FIREFOX_MAJORS)

    categories_mapping.append((ProductCategory.MAJOR,
                               r'([0-9]+\.[0-9]+%s)$' % special_majors))
    categories_mapping.append((ProductCategory.MAJOR,
                               r'([0-9]+\.[0-9]+(esr|)%s)$' % special_majors))
    categories_mapping.append((ProductCategory.STABILITY,
                               r'([0-9]+\.[0-9]+\.[0-9]+$|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$)'))
    categories_mapping.append((ProductCategory.STABILITY,
                               r'([0-9]+\.[0-9]+\.[0-9]+(esr|)$|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(esr|)$)'))
    # We had 38.0.5b2
    categories_mapping.append((ProductCategory.DEVELOPMENT,
                               r'([0-9]+\.[0-9]|[0-9]+\.[0-9]+\.[0-9])(b|rc|build|plugin)[0-9]+$'))

    # Ugly hack to manage the next ESR (when we have two overlapping esr)
    if shipit_api.config.ESR_NEXT:
        categories_mapping.append((ProductCategory.ESR,
                                   shipit_api.config.ESR_NEXT + r'(\.[0-9]+){1,2}esr$'))
    else:
        categories_mapping.append((ProductCategory.ESR,
                                   shipit_api.config.CURRENT_ESR + r'(\.[0-9]+){1,2}esr$'))

    for (product_category, version_pattern) in categories_mapping:
        if re.match(version_pattern, version):
            categories.append(product_category)

    return categories


def get_releases(breakpoint_version: int,
                 products: Products,
                 releases: typing.List[shipit_api.models.Release],
                 old_product_details: ProductDetails,
                 ) -> Releases:
    '''This file holds historical information about all Firefox, Firefox for
       Mobile (aka Fennec), Firefox Dev Edition and Thunderbird releases we
       shipped in the past.

       This function will output to the following files:
        - all.json
        - devedition.json
        - firefox.json
        - mobile_android.json
        - thunderbird.json

       Example:::

           "firefox-58.0": {
               "category":           "major",
               "product":            "firefox",
               "build_number":       6,
               "description":        "",
               "is_security_driven": false,
               "version":            "58.0",
               "date":               "2018-01-23",
           }
    '''
    details = dict()

    for product in products:

        #
        # get release details from the JSON files up to breakpoint_version
        #
        product_file = f'1.0/{product.value}.json'
        if product is Product.FENNEC:
            product_file = '1.0/mobile_android.json'

        old_releases = typing.cast(typing.Dict[str, ReleaseDetails], old_product_details[product_file].get('releases', dict()))  # noqa
        for product_with_version in old_releases:
            # mozilla_version.gecko.GeckoVersion does not parse rc (yet)
            # https://github.com/mozilla-releng/mozilla-version/pull/40
            #
            # version = get_product_mozilla_version(product, product_with_version[len(product.value) + 1:])
            # if version.major_number >= breakpoint_version:
            version = int(product_with_version[len(product.value) + 1:].split('.')[0])
            if version >= breakpoint_version:
                continue
            details[product_with_version] = old_releases[product_with_version]

        #
        # get release history from the database
        #
        for release in releases:
            if release.product != product.value:
                continue
            categories = get_product_categories(Product(release.product), release.version)
            release_version = release.version
            for category in categories:
                if release_version.endswith('esr'):
                    release_version = release_version[:-len('esr')]
                details[f'{release.product}-{release.version}'] = dict(
                    category=category.value,
                    product=release.product,
                    build_number=release.build_number,
                    description=None,
                    is_security_driven=False,  # TODO: we don't have this field anymore
                    version=release_version,
                    date=with_default(release.completed,
                                      functools.partial(to_format, format='YYYY-MM-DD'),
                                      default='',
                                      ),
                )

    return dict(releases=details)


def get_release_history(breakpoint_version: int,
                        product: Product,
                        product_category: ProductCategory,
                        releases: typing.List[shipit_api.models.Release],
                        old_product_details: ProductDetails) -> ReleasesHistory:
    '''This file contains all the Product release dates for releases in that
       category.

       This function will output to the following files:
        - firefox_history_development_releases.json
        - firefox_history_major_releases.json
        - firefox_history_stability_releases.json
        - mobile_history_development_releases.json
        - mobile_history_major_releases.json
        - mobile_history_stability_releases.json
        - thunderbird_history_development_releases.json
        - thunderbird_history_major_releases.json
        - thunderbird_history_stability_releases.json

       Example:::

           {
               ...
               "59.0b11": "2018-02-20",
               "59.0b12": "2018-02-23",
               "59.0b13": "2018-02-27",
               "59.0b14": "2018-03-02",
               ...
           }
    '''
    if Product.DEVEDITION is product:
        raise click.ClickException(f'We don\'t generate product history for "{product.value}" product.')

    if ProductCategory.ESR is product_category:
        raise click.ClickException(f'We don\'t generate product history for "{product_category.value}" product category.')

    history = dict()

    #
    # get release history from the JSON files up to breakpoint_version
    #
    product_file = f'1.0/{product.value}_history_{product_category.name.lower()}_releases.json'
    if product is Product.FENNEC:
        product_file = f'1.0/mobile_history_{product_category.name.lower()}_releases.json'

    old_history = typing.cast(ReleasesHistory, old_product_details[product_file])
    for product_with_version in old_history:
        # mozilla_version.gecko.GeckoVersion does not parse rc (yet)
        # https://github.com/mozilla-releng/mozilla-version/pull/40
        #
        # version = get_product_mozilla_version(product, product_with_version[len(product.value) + 1:])
        # if version.major_number >= breakpoint_version:
        version = int(product_with_version.split('.')[0])
        if version >= breakpoint_version:
            continue
        history[product_with_version] = old_history[product_with_version]

    #
    # get release history from the database
    #
    for release in releases:
        if product.value != release.product:
            continue

        if release.status != 'shipped':
            continue

        release_version = get_product_mozilla_version(Product(release.product), release.version)
        if release_version is None or release_version.major_number < breakpoint_version:
            continue

        # skip all releases which don't fit into product category
        if product_category is ProductCategory.MAJOR and \
                (release_version.patch_number is not None or release_version.beta_number is not None or release_version.is_esr):
            continue

        elif product_category is ProductCategory.DEVELOPMENT and \
                (release_version.beta_number is None or release_version.is_esr):
            continue

        elif product_category is ProductCategory.STABILITY and \
                (release_version.beta_number is not None or release_version.patch_number is None):
            continue

        history_version = release.version
        if history_version.endswith('esr'):
            history_version = history_version[:-len('esr')]

        history[history_version] = with_default(release.completed,
                                                functools.partial(to_format, format='YYYY-MM-DD'),
                                                default='',
                                                )

    return history


def get_primary_builds(breakpoint_version: int,
                       product: Product,
                       releases: typing.List[shipit_api.models.Release],
                       releases_l10n: typing.Dict[shipit_api.models.Release, ReleaseL10ns],
                       old_product_details: ProductDetails) -> PrimaryBuilds:
    '''This file contains all the Thunderbird builds we provide per locale. The
       filesize fields have the same value for all lcoales, this is not a bug,
       we are keeping these fields with this schema for historical reasons only
       but no longer populate them with fresh data.

       This function will output to the following files:
        - firefox_primary_builds.json
        - thunderbird_primary_builds.json

       Example:::

           {
               "el": {
                   "52.6.0": {
                       "Windows": {
                           "filesize": 25.1,
                       },
                       "OS X": {
                           "filesize": 50.8,
                       },
                       "Linux": {
                           "filesize": 31.8,
                       },
                   },
               }
           }
    '''

    if product is Product.FIREFOX:
        firefox_versions = get_firefox_versions(releases)
        versions = [
            firefox_versions['FIREFOX_NIGHTLY'],
            firefox_versions['LATEST_FIREFOX_RELEASED_DEVEL_VERSION'],
            firefox_versions['LATEST_FIREFOX_VERSION'],
            firefox_versions['FIREFOX_ESR'],
        ]
    elif product is Product.THUNDERBIRD:
        thunderbird_versions = get_thunderbird_versions(releases)
        versions = [
            thunderbird_versions['LATEST_THUNDERBIRD_VERSION'],
            thunderbird_versions['LATEST_THUNDERBIRD_ALPHA_VERSION'],
            thunderbird_versions['LATEST_THUNDERBIRD_DEVEL_VERSION'],
            thunderbird_versions['LATEST_THUNDERBIRD_NIGHTLY_VERSION'],
        ]
    else:
        raise click.ClickException(f'We don\'t generate product history for "{product.value}" product.')

    builds: PrimaryBuilds = dict()

    for release in releases:
        if product is not Product(release.product) or \
           release.version in versions:
            continue
        for l10n in releases_l10n.get(release, {}).keys():
            builds.setdefault(l10n, dict())
            for version in versions:
                if version == '':
                    continue
                if product is Product.THUNDERBIRD:
                    builds[l10n][version] = {
                        'Windows': {
                            'filesize': 25.1
                        },
                        'OS X': {
                            'filesize': 50.8
                        },
                        'Linux': {
                            'filesize': 31.8
                        }
                    }
                else:
                    builds[l10n][version] = {
                        'Windows': {
                            'filesize': 0,
                        },
                        'OS X': {
                            'filesize': 0,
                        },
                        'Linux': {
                            'filesize': 0,
                        },
                    }

    return builds


def get_latest_version(releases: typing.List[shipit_api.models.Release],
                       branch: str,
                       product: Product
                       ) -> str:
    '''Get latest version

    Get the latest shipped version for a particular branch/product,
    optionally for a particular major version. The results should be sorted
    by version, not by date, because we may publish a correction release
    for old users (this has been done in the past).
    '''
    filtered_releases = [r for r in releases if
                         r.product == product.value and
                         r.branch == branch]
    releases_ = sorted(
        filtered_releases,
        reverse=True,
        key=lambda r: get_product_mozilla_version(Product(product), r.version))
    if len(releases_) == 0:
        # XXX: should we fallback to old_product_details?
        return ''
    return releases_[0].version


def get_firefox_esr_version(releases: typing.List[shipit_api.models.Release],
                            branch: str,
                            product: Product
                            ) -> str:
    '''Return latest ESR version

    Get the latest version using CURRENT_ESR major version. Sometimes, when we
    have 2 overlapping ESR releases we want to point this to the older version,
    while ESR_NEXT will be pointing to the next release.
    '''
    return get_latest_version(releases, branch, product)


def get_firefox_esr_next_version(releases: typing.List[shipit_api.models.Release],
                                 branch: str,
                                 product: Product,
                                 esr_next: typing.Optional[str],
                                 ) -> str:
    '''Next ESR version

    Return an empty string when there is only one ESR release published. If
    ESR_NEXT is set to a false value, return an empty string. Otherwise get
    latest version for ESR_NEXT major version.
    '''
    if not esr_next:
        return ''
    else:
        return get_latest_version(releases, branch, product)


def get_firefox_versions(releases: typing.List[shipit_api.models.Release]) -> FirefoxVersions:
    '''All the versions we ship for Firefox for Desktop

       This function will output to the following files:
        - firefox_versions.json

       Example:::
           {
               "FIREFOX_NIGHTLY":                        "60.0a1",
               "FIREFOX_AURORA":                         "",
               "FIREFOX_ESR":                            "52.6.0esr",
               "FIREFOX_ESR_NEXT":                       "",
               "LATEST_FIREFOX_DEVEL_VERSION":           "59.0b14",
               "FIREFOX_DEVEDITION":                     "59.0b14",
               "LATEST_FIREFOX_OLDER_VERSION":           "3.6.28",
               "LATEST_FIREFOX_RELEASED_DEVEL_VERSION":  "59.0b14",
               "LATEST_FIREFOX_VERSION":                 "58.0.2",
           }
    '''

    return dict(
        FIREFOX_NIGHTLY=shipit_api.config.FIREFOX_NIGHTLY,
        FIREFOX_AURORA=shipit_api.config.FIREFOX_AURORA,
        LATEST_FIREFOX_VERSION=get_latest_version(releases,
                                                  shipit_api.config.RELEASE_BRANCH,
                                                  Product.FIREFOX,
                                                  ),
        FIREFOX_ESR=get_firefox_esr_version(releases,
                                            f'{shipit_api.config.ESR_BRANCH_PREFIX}{shipit_api.config.CURRENT_ESR}',
                                            Product.FIREFOX,
                                            ),
        FIREFOX_ESR_NEXT=get_firefox_esr_next_version(releases,
                                                      f'{shipit_api.config.ESR_BRANCH_PREFIX}{shipit_api.config.ESR_NEXT}',
                                                      Product.FIREFOX,
                                                      shipit_api.config.ESR_NEXT,
                                                      ),
        LATEST_FIREFOX_DEVEL_VERSION=get_latest_version(releases,
                                                        shipit_api.config.BETA_BRANCH,
                                                        Product.FIREFOX,
                                                        ),
        LATEST_FIREFOX_RELEASED_DEVEL_VERSION=get_latest_version(releases,
                                                                 shipit_api.config.BETA_BRANCH,
                                                                 Product.FIREFOX,
                                                                 ),
        FIREFOX_DEVEDITION=get_latest_version(releases,
                                              shipit_api.config.BETA_BRANCH,
                                              Product.DEVEDITION,
                                              ),
        LATEST_FIREFOX_OLDER_VERSION=shipit_api.config.LATEST_FIREFOX_OLDER_VERSION,
        NEXT_SOFTFREEZE_DATE=shipit_api.config.NEXT_SOFTFREEZE_DATE,
        NEXT_MERGE_DATE=shipit_api.config.NEXT_MERGE_DATE,
        NEXT_RELEASE_DATE=shipit_api.config.NEXT_RELEASE_DATE,
    )


def get_regions(old_product_details: ProductDetails) -> ProductDetails:
    '''The files in this folder store the localized names for countries. The
       data was extracted from our Gecko localization files and converted to
       JSON as we needed it for projects that needed to associate product and
       regional data. Those files are updated by the l10n-drivers team.

       This function will output to the following files:
        - regions.json

       Example:::

           {
               "af": "Afghanistan",
               "za": "Afrique du Sud",
               "qz": "Akrotiri",
               "al": "Albanie",
               ...
           }
    '''
    regions: ProductDetails = dict()
    for file_, content in old_product_details.items():
        if file_.startswith('1.0/regions/'):
            regions[file_[len('1.0/'):]] = content
    return regions


def get_l10n(releases: typing.List[shipit_api.models.Release],
             releases_l10n: typing.Dict[shipit_api.models.Release, ReleaseL10ns],
             old_product_details: ProductDetails,
             ) -> ProductDetails:
    '''This folder contains the l10n changeset per locale used for each build.
       The translation of our products is done in separate l10n repositories,
       each locale provides a good known version of their translations through
       a sign off process with l10n-drivers and these changeset per locale are
       used to build Firefox, Thunderbird and Fennec.

       This function will output to the following files:
        - l10n/<file>.json

       Example for l10n/Firefox-58.0-build6.json file:::
           {
               "locales": {
                   "pa-IN": {
                       "changeset": "5634ac6e7d9b",
                   },
                   "gd": {
                       "changeset": "da7de9b6e635",
                   },
                   …
               },
               "submittedAt": "2018-01-18T22:53:08+00:00",
               "shippedAt": "2018-01-23T13:20:26+00:00",
               "name": "Firefox-58.0-build6",
           }
    '''
    # populate with old data first, stripping the '1.0/' prefix
    data: ProductDetails = {
        file_.replace('1.0/', ''): content
        for file_, content in old_product_details.items()
        if file_.startswith('1.0/l10n/')
    }

    for (release, locales) in releases_l10n.items():
        # XXX: for some reason we didn't generate l10n for devedition in old_product_details
        if Product(release.product) is Product.DEVEDITION:
            continue
        data[f'l10n/{release.name}.json'] = {
            'locales': {
                locale: dict(changeset=content['revision'])
                for locale, content in locales.items()
            },
            'submittedAt': with_default(release.created, to_isoformat, default=''),
            'shippedAt': with_default(release.completed, to_isoformat, default=''),
            'name': release.name,
        }

    return data


def get_languages(old_product_details: ProductDetails) -> Languages:
    '''List of all the supported BCP-47 locales with their English and native names.

       This function will output to the following files:
        - languages.json

       Example:::

           {
               "cs": {
                   "English": "Czech",
                   "native":  "Čeština",
               },
               "csb": {
                   "English": "Kashubian",
                   "native":  "Kaszëbsczi",
               },
               "cy": {
                   "English": "Welsh",
                   "native":  "Cymraeg",
               },
               ...
           }

    '''
    languages = old_product_details.get('1.0/languages.json')

    if languages is None:
        raise click.ClickException('"1.0/languages.json" does not exists in old product details"')

    # I can not use isinstance with generics (like Languages) for this reason
    # I'm casting to output type
    # https://gist.github.com/garbas/0cf4b6c3c34d1aa311225df283db19a6

    return typing.cast(Languages, languages)


def get_mobile_details(releases: typing.List[shipit_api.models.Release]) -> MobileDetails:
    '''This file contains all the release information for Firefox for Android
       and Firefox for iOS. We are keeping this file around for backward
       compatibility with consumers and only the version numbers are updated
       today. The builds, beta_builds and alpha_builds sections are static.

       If you are interested in getting the version number we ship per channel
       use mobile_versions.json instead of this file.

       This function will output to the following files:
        - mobile_details.json

       Example:::
           {
               "nightly_version": "60.0a1",
               "alpha_version": "60.0a1",
               "beta_version": "59.0b13",
               "version": "58.0.2",
               "ios_beta_version": "9.1",
               "ios_version": "9.0",
               "builds": [
                       {
                           "locale": {
                               "code": "ar",
                               "english": "Arabic",
                               "native": "\u0639\u0631\u0628\u064a"
                           }
                       },
                       {
                           "locale": {
                               "code": "be",
                               "english": "Belarusian",
                               "native": "\u0411\u0435\u043b\u0430\u0440\u0443\u0441\u043a\u0430\u044f"
                           }
                       },
                       …
                   ],
               "beta_builds": [
                   {
                       "locale": {
                           "code": "cs",
                           "english": "Czech",
                           "native": "\u010ce\u0161tina"
                       },
                       "download": {
                           "android": "market://details?id=org.mozilla.firefox_beta"
                       }
                   },
                   {
                       "locale": {
                           "code": "de",
                           "english": "German",
                           "native": "Deutsch"
                       },
                       "download": {
                           "android": "market://details?id=org.mozilla.firefox_beta"
                       }
                   },
                   …
               ],
               "alpha_builds": [
                   {
                       "locale": {
                           "code": "en-US",
                           "english": "English (US)",
                           "native": "English (US)"
                       },
                       "download": {
                           "android": "market://details?id=org.mozilla.firefox"
                       }
                   }
               ]
               },
           }
    '''
    mobile_versions = get_mobile_versions(releases)
    mobile_details = json.loads(shipit_api.config.MOBILE_DETAILS_TEMPLATE)
    mobile_details.update(mobile_versions)
    return mobile_details


def get_mobile_versions(releases: typing.List[shipit_api.models.Release]) -> MobileVersions:
    '''This file contains all the versions we ship for Firefox for Android

       This function will output to the following files:
        - mobile_versions.json

       Example:::

           {
               "nightly_version": "60.0a1",
               "alpha_version": "60.0a1",
               "beta_version": "59.0b13",
               "version": "58.0.2",
               "ios_beta_version": "9.1",
               "ios_version": "9.0",
           }
    '''
    return dict(
        ios_beta_version=shipit_api.config.IOS_BETA_VERSION,
        ios_version=shipit_api.config.IOS_VERSION,
        nightly_version=shipit_api.config.FIREFOX_NIGHTLY,
        alpha_version=shipit_api.config.FIREFOX_NIGHTLY,
        beta_version=get_latest_version(releases,
                                        shipit_api.config.BETA_BRANCH,
                                        Product.FENNEC,
                                        ),
        version=get_latest_version(releases,
                                   shipit_api.config.RELEASE_BRANCH,
                                   Product.FENNEC,
                                   ),
    )


def get_thunderbird_versions(releases: typing.List[shipit_api.models.Release]) -> ThunderbirdVersions:
    '''

       This function will output to the following files:
        - thunderbird_versions.json

       Example:::

           {
               "LATEST_THUNDERBIRD_VERSION":         "52.6.0",
               "LATEST_THUNDERBIRD_ALPHA_VERSION":   "54.0a2",
               "LATEST_THUNDERBIRD_DEVEL_VERSION":   "59.0b2",
               "LATEST_THUNDERBIRD_NIGHTLY_VERSION": "60.0a1"
           }
    '''
    return dict(
        LATEST_THUNDERBIRD_VERSION=get_latest_version(releases,
                                                      shipit_api.config.THUNDERBIRD_RELEASE_BRANCH,
                                                      Product.THUNDERBIRD,
                                                      ),
        LATEST_THUNDERBIRD_DEVEL_VERSION=get_latest_version(releases,
                                                            shipit_api.config.THUNDERBIRD_BETA_BRANCH,
                                                            Product.THUNDERBIRD,
                                                            ),
        LATEST_THUNDERBIRD_NIGHTLY_VERSION=shipit_api.config.LATEST_THUNDERBIRD_NIGHTLY_VERSION,
        LATEST_THUNDERBIRD_ALPHA_VERSION=shipit_api.config.LATEST_THUNDERBIRD_ALPHA_VERSION,
    )


def get_thunderbird_beta_builds() -> typing.Dict:
    '''This file is empty and not used today.

       This function will output to the following files:
        - thunderbird_beta_builds.json

       Example:::

           {}
    '''
    return dict()


def run_check(*arg, **kw):
    return cli_common.utils.retry(lambda: cli_common.command.run_check(*arg, **kw))


async def rebuild(db_session: sqlalchemy.orm.Session,
                  git_branch: str,
                  git_repo_url: str,
                  folder_in_repo: str,
                  breakpoint_version: typing.Optional[int],
                  clean_working_copy: bool = True,
                  ):

    secrets = [urllib.parse.urlparse(git_repo_url).password]

    # Sometimes we want to work from a clean working copy
    if clean_working_copy and shipit_api.config.PRODUCT_DETAILS_DIR.exists():
        shutil.rmtree(shipit_api.config.PRODUCT_DETAILS_DIR)

    # Clone/pull latest product details
    logger.info(f'Getting latest product details from {git_repo_url}.')
    if shipit_api.config.PRODUCT_DETAILS_DIR.exists():
        # Checkout the branch we are working on
        logger.info(f'Checkout {git_branch} branch.')
        run_check(['git', 'checkout', git_branch],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        run_check(['git', 'pull'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        # make sure checkout is clean by removing changes to existing files
        run_check(['git', 'reset', '--hard', 'HEAD'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        # make sure checkout is clean by removing files which are new
        run_check(['git', 'clean', '-xfd'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
    else:
        run_check(['git', 'clone', git_repo_url, shipit_api.config.PRODUCT_DETAILS_DIR.name],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR.parent,
                  secrets=secrets,
                  )
        run_check(['git', 'config', 'http.postBuffer', '12M'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        run_check(['git', 'config', 'user.email', 'release-services+robot@mozilla.com'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        run_check(['git', 'config', 'user.name', 'Release Services Robot'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        # Checkout the branch we are working on
        logger.info(f'Checkout {git_branch} branch.')
        run_check(['git', 'checkout', '-b', git_branch, f'origin/{git_branch}'],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )

    # XXX: we need to implement how to figure out breakpoint_version from old_product_details
    # if breakpoint_version is not provided we should figure it out from old_product_details
    # and if we can not figure it out we should use shipit_api.config.BREAKPOINT_VERSION
    # breakpoint_version should always be higher then shipit_api.config.BREAKPOINT_VERSION
    if breakpoint_version is None:
        breakpoint_version = shipit_api.config.BREAKPOINT_VERSION
    logger.info(f'Breakpoint version is {breakpoint_version}')

    # get data from older product-details
    logger.info(f'Reading old product details from {shipit_api.config.PRODUCT_DETAILS_DIR / folder_in_repo}')
    old_product_details = get_old_product_details(
        shipit_api.config.PRODUCT_DETAILS_DIR / folder_in_repo)

    # get all the releases from the database from (including)
    # breakpoint_version on
    logger.info(f'Getting old releases from the database')
    releases = get_releases_from_db(db_session, breakpoint_version)

    # get all the l10n for each release from the database
    # use limit_per_host=50 since hg.mozilla.org doesn't like too many connections
    logger.info(f'Getting locales from hg.mozilla.org for each release from database')
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=50)) as session:
        releases_l10n = await asyncio.gather(*[
            fetch_l10n_data(session, release, git_branch)
            for release in releases
        ])
    releases_l10n = {
        release: changeset
        for (release, changeset) in releases_l10n
        if changeset is not None
    }

    # combine old and new data
    product_details: ProductDetails = {
        'all.json': get_releases(breakpoint_version,
                                 [i for i in list(Product)],
                                 releases,
                                 old_product_details,
                                 ),
        'devedition.json': get_releases(breakpoint_version,
                                        [Product.DEVEDITION],
                                        releases,
                                        old_product_details,
                                        ),
        'firefox.json': get_releases(breakpoint_version,
                                     [Product.FIREFOX],
                                     releases,
                                     old_product_details,
                                     ),
        'firefox_history_development_releases.json': get_release_history(breakpoint_version,
                                                                         Product.FIREFOX,
                                                                         ProductCategory.DEVELOPMENT,
                                                                         releases,
                                                                         old_product_details,
                                                                         ),
        'firefox_history_major_releases.json': get_release_history(breakpoint_version,
                                                                   Product.FIREFOX,
                                                                   ProductCategory.MAJOR,
                                                                   releases,
                                                                   old_product_details,
                                                                   ),
        'firefox_history_stability_releases.json': get_release_history(breakpoint_version,
                                                                       Product.FIREFOX,
                                                                       ProductCategory.STABILITY,
                                                                       releases,
                                                                       old_product_details,
                                                                       ),
        'firefox_primary_builds.json': get_primary_builds(breakpoint_version,
                                                          Product.FIREFOX,
                                                          releases,
                                                          releases_l10n,
                                                          old_product_details,
                                                          ),
        'firefox_versions.json': get_firefox_versions(releases),
        'languages.json': get_languages(old_product_details),
        'mobile_android.json': get_releases(breakpoint_version,
                                            [Product.FENNEC],
                                            releases,
                                            old_product_details,
                                            ),
        'mobile_details.json': get_mobile_details(releases),
        'mobile_history_development_releases.json': get_release_history(breakpoint_version,
                                                                        Product.FENNEC,
                                                                        ProductCategory.DEVELOPMENT,
                                                                        releases,
                                                                        old_product_details,
                                                                        ),
        'mobile_history_major_releases.json': get_release_history(breakpoint_version,
                                                                  Product.FENNEC,
                                                                  ProductCategory.MAJOR,
                                                                  releases,
                                                                  old_product_details,
                                                                  ),
        'mobile_history_stability_releases.json': get_release_history(breakpoint_version,
                                                                      Product.FENNEC,
                                                                      ProductCategory.STABILITY,
                                                                      releases,
                                                                      old_product_details,
                                                                      ),
        'mobile_versions.json': get_mobile_versions(releases),
        'thunderbird.json': get_releases(breakpoint_version,
                                         [Product.THUNDERBIRD],
                                         releases,
                                         old_product_details,
                                         ),
        'thunderbird_beta_builds.json': get_thunderbird_beta_builds(),
        'thunderbird_history_development_releases.json': get_release_history(breakpoint_version,
                                                                             Product.THUNDERBIRD,
                                                                             ProductCategory.DEVELOPMENT,
                                                                             releases,
                                                                             old_product_details,
                                                                             ),
        'thunderbird_history_major_releases.json': get_release_history(breakpoint_version,
                                                                       Product.THUNDERBIRD,
                                                                       ProductCategory.MAJOR,
                                                                       releases,
                                                                       old_product_details,
                                                                       ),
        'thunderbird_history_stability_releases.json': get_release_history(breakpoint_version,
                                                                           Product.THUNDERBIRD,
                                                                           ProductCategory.STABILITY,
                                                                           releases,
                                                                           old_product_details,
                                                                           ),
        'thunderbird_primary_builds.json': get_primary_builds(breakpoint_version,
                                                              Product.THUNDERBIRD,
                                                              releases,
                                                              releases_l10n,
                                                              old_product_details,
                                                              ),
        'thunderbird_versions.json': get_thunderbird_versions(releases),
    }

    product_details.update(get_regions(old_product_details))
    product_details.update(get_l10n(releases, releases_l10n, old_product_details))

    #  add '1.0/' infront of each file path
    product_details = {
        f'1.0/{file_}': content
        for file_, content in product_details.items()
    }

    # create index.html for every folder
    product_details = create_index_listing(product_details)

    if shipit_api.config.PRODUCT_DETAILS_NEW_DIR.exists():
        shutil.rmtree(shipit_api.config.PRODUCT_DETAILS_NEW_DIR)

    for (file__, content) in product_details.items():
        new_file = shipit_api.config.PRODUCT_DETAILS_NEW_DIR / file__

        # we must ensure that all needed folders exists
        os.makedirs(new_file.parent, exist_ok=True)

        # write content into json file
        with new_file.open('w+') as f:
            if new_file.suffix == '.json':
                f.write(json.dumps(content, sort_keys=True, indent=4))
            else:
                f.write(content)

    # remove all top level items in folder_in_repo
    for item in os.listdir(shipit_api.config.PRODUCT_DETAILS_DIR / folder_in_repo):
        item = shipit_api.config.PRODUCT_DETAILS_DIR / folder_in_repo / item
        if item.exists():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                os.unlink(item)

    # Move new files to be commited
    for item in os.listdir(shipit_api.config.PRODUCT_DETAILS_NEW_DIR):
        shutil.move(
            shipit_api.config.PRODUCT_DETAILS_NEW_DIR / item,
            shipit_api.config.PRODUCT_DETAILS_DIR / folder_in_repo / item,
        )

    # Add, commit and push changes
    run_check(['git', 'add', '.'],
              cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
              secrets=secrets,
              )

    # check if there is something to commit
    output = run_check(['git', 'status', '--short'],
                       cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                       secrets=secrets,
                       )
    if output != b'':
        # XXX: we need a better commmit message, maybe mention what triggered this update
        commit_message = 'Updating product details'
        run_check(['git', 'commit', '-m', commit_message],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
        run_check(['git', 'push', 'origin', git_branch],
                  cwd=shipit_api.config.PRODUCT_DETAILS_DIR,
                  secrets=secrets,
                  )
