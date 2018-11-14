# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import enum
import functools
import io
import json
import os
import pathlib
import re
import shutil
import tempfile
import typing

import aiohttp
import awscli
import click
import flask
import mohawk
import mozilla_version.gecko
import mypy_extensions
import requests
import sqlalchemy
import sqlalchemy.orm
import typeguard

import shipit_api.config
import shipit_api.models


def coroutine(f):
    f = asyncio.coroutine(f)

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return functools.update_wrapper(wrapper, f)


async def download_json_file(session, url, file_):
    click.echo(f'=> Downloading {url}')
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()

        content = await response.text()

        file_dir = os.path.dirname(file_)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        with io.open(file_, 'w+') as f:
            f.write(content)
        click.echo(f'=> Downloaded to {file_}')

        return (url, file_)


@click.command(name='upload-product-details')
@click.option(
    '--download-dir',
    required=True,
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        readable=True,
    ),
)
@click.option(
    '--shipit-url',
    default='https://ship-it.mozilla.org',
)
@coroutine
async def download_product_details(shipit_url: str, download_dir: str):

    if os.path.isdir(download_dir):
        shutil.rmtree(download_dir)
        os.makedirs(download_dir)

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{shipit_url}/json_exports.json') as response:
            if response.status != 200:
                response.raise_for_status()
            json_paths = await response.json()

        await asyncio.gather(*[
            download_json_file(
                session,
                f'{shipit_url}{json_path}',
                f'{download_dir}{json_path}',
            )
            for json_path in json_paths
        ])

    click.echo('All files were downloaded successfully!')


@enum.unique
class Product(enum.Enum):
    DEVEDITION = 'devedition'
    FIREFOX = 'firefox'
    FENNEC = 'fennec'
    THUNDERBIRD = 'thunderbird'


@enum.unique
class ProductCategory(enum.Enum):
    MAJOR = 'major'
    DEVELOPMENT = 'development'
    STABILITY = 'stability'
    ESR = 'esr'


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


File = str
ReleaseDetails = mypy_extensions.TypedDict('ReleaseDetails', {
    'category': str,
    'product': str,
    'build_number': int,
    'description': str,
    'is_security_driven': bool,
    'version': str,
    'date': str,
})
Releases = mypy_extensions.TypedDict('Releases', {
  'releases': typing.Dict[str, ReleaseDetails],
})
ReleasesHistory = typing.Dict[str, str]
PrimaryBuildDetails = mypy_extensions.TypedDict('PrimaryBuildDetails', {
    'filesize': int,
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
]]
Products = typing.List[Product]


def get_old_product_details(directory: str) -> ProductDetails:

    if not os.path.isdir(directory):
        return dict()

    data = dict()
    for root_, _, files in os.walk(directory):
        root = pathlib.Path(root_)
        for file__ in files:
            file_ = root / file__
            with file_.open() as f:
                data[str(file_.relative_to(directory))] = json.load(f)

    return data


def get_releases_from_db(db_session: sqlalchemy.orm.Session,
                         breakpoint_version: typing.Optional[int]=None,
                         ) -> typing.List[shipit_api.models.Release]:
    '''
     SELECT *
     FROM shipit_api_releases as r
     WHERE cast(split_part(r.version, '.', 1) as int) > 20;
    '''
    Release = shipit_api.models.Release
    query = db_session.query(Release)
    if breakpoint_version:
        # Using cast and split_part is postgresql specific
        query = query.filter(
            sqlalchemy.cast(
                sqlalchemy.func.split_part(Release.version, '.', 1),
                sqlalchemy.Integer) >= breakpoint_version)
    return query.all()


def get_product_l10n(product: Product,
                     version: str,
                     ) -> typing.List[str]:
    return []  # TODO: not implemented


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
        product_file = f'json/1.0/{product.value}.json'
        if product is Product.FENNEC:
            product_file = 'json/1.0/mobile_android.json'

        old_releases = typing.cast(typing.Dict[str, ReleaseDetails], old_product_details[product_file].get('releases', dict()))
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
            categories = get_product_categories(Product(release.product), release.version)
            for category in categories:
                details[f'{release.product}-{release.version}'] = dict(
                    category=category.value,
                    product=release.product,
                    build_number=release.build_number,
                    description='',  # XXX: we don't have this field anymore
                    is_security_driven=False,  # XXX: we don't have this field anymore
                    version=release.version,
                    date=release.completed.strftime('%Y-%m-%d'),
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
    product_file = f'json/1.0/{product.value}_history_{product_category.value}_releases.json'
    if product is Product.FENNEC:
        product_file = f'json/1.0/mobile_history_{product_category.value}_releases.json'

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

        version = int(release.version.split('.')[0])
        if version < breakpoint_version:
            continue

        history[release.version] = release.completed.strftime('%Y-%m-%d')

    return history  # TODO: not implemented


def get_primary_builds(breakpoint_version: int,
                       product: Product,
                       releases: typing.List[shipit_api.models.Release],
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

    for version in versions:
        for l10n in get_product_l10n(product, version):
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


def get_latest_version(releases: typing.List[shipit_api.models.Release], branch: str, product: Product):
    '''Get latest version

    Get the latest shipped version for a particular branch/product,
    optionally for a particular major version. The results should be sorted
    by version, not by date, because we may publish a correction release
    for old users (this has been done in the past).
    '''
    filtered_releases = [r for r in releases if
                         r.product == product.value and
                         r.branch == branch and
                         r.status == 'shipped']
    releases = sorted(
        filtered_releases,
        reverse=True,
        key=lambda r: get_product_mozilla_version(Product(product), r.version))
    if releases:
        return releases[0].version
    else:
        # TODO: raise
        return None


def get_firefox_esr_version(releases: typing.List[shipit_api.models.Release], branch, product):
    '''Return latest ESR version

    Get the latest version using CURRENT_ESR major version. Sometimes, when we
    have 2 overlapping ESR releases we want to point this to the older version,
    while ESR_NEXT will be pointing to the next release.
    '''
    return get_latest_version(releases, branch, product)


def get_firefox_esr_next_version(releases: typing.List[shipit_api.models.Release], branch, product, esr_next):
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
        LATEST_FIREFOX_VERSION=get_latest_version(
            releases, shipit_api.config.RELEASE_BRANCH, Product.FIREFOX),
        FIREFOX_ESR=get_firefox_esr_version(
            releases,
            f'{shipit_api.config.ESR_BRANCH_PREFIX}{shipit_api.config.CURRENT_ESR}',
            Product.FIREFOX),
        FIREFOX_ESR_NEXT=get_firefox_esr_next_version(
            releases,
            f'{shipit_api.config.ESR_BRANCH_PREFIX}{shipit_api.config.ESR_NEXT}',
            Product.FIREFOX, shipit_api.config.ESR_NEXT),
        LATEST_FIREFOX_DEVEL_VERSION=get_latest_version(
            releases, shipit_api.config.BETA_BRANCH, Product.FIREFOX),
        LATEST_FIREFOX_RELEASED_DEVEL_VERSION=get_latest_version(
            releases, shipit_api.config.BETA_BRANCH, Product.FIREFOX),
        FIREFOX_DEVEDITION=get_latest_version(releases, shipit_api.config.BETA_BRANCH, Product.DEVEDITION),
        LATEST_FIREFOX_OLDER_VERSION=shipit_api.config.LATEST_FIREFOX_OLDER_VERSION,
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
    # TODO: can we fetch regions from somewhere else
    regions = dict()
    for file_, content in old_product_details.items():
        if not (file_.startswith('json/1.0/regions/')
                and typeguard.check_type('file_', file_, File)
                and typeguard.check_type('content', content, Region)):
            continue
        regions[file_] = content
    return regions


def get_l10n(
        all_releases: typing.List[shipit_api.models.Release],
        releases: typing.List[shipit_api.models.Release],
        old_product_details: ProductDetails) -> ProductDetails:
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
    ret = {}
    filtered_releases = [r for r in all_releases if r.status == 'shipped']
    new_release_names = [r.name for r in releases]
    for release in filtered_releases:
        old_file_path = f'json/1.0/l10n/{release.name}.json'
        new_file_path = f'l10n/{release.name}.json'
        if old_product_details.get(old_file_path):
            ret[new_file_path] = old_product_details[old_file_path]
        elif release.name not in new_release_names:
            # this is an old version, and it's not in the old data, ignore
            pass
        else:
            # TODO: very expesive call to HG
            ret[new_file_path] = dict()
    return ret


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
    # TODO: can we fetch languages from somewhere else
    languages = old_product_details.get('json/1.0/languages.json')

    if languages is None:
        raise click.ClickException('"json/1.0/languages.json" does not exists in old product details"')

    # I can not use isinstance with generics (like Languages) for this reason
    # I'm casting to output type
    # https://gist.github.com/garbas/0cf4b6c3c34d1aa311225df283db19a6

    return typing.cast(Languages, languages)


def get_mobile_details(old_product_details: ProductDetails) -> MobileDetails:
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
    # TODO: not implemented
    return dict(
        nightly_version='60.0a1',
        alpha_version='60.0a1',
        beta_version='59.0b13',
        version='58.0.2',
        ios_beta_version='9.1',
        ios_version='9.0',
        builds=[],
        beta_builds=[],
        alpha_builds=[],
    )


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
        beta_version=get_latest_version(releases, shipit_api.config.BETA_BRANCH, Product.FENNEC),
        version=get_latest_version(releases, shipit_api.config.RELEASE_BRANCH, Product.FENNEC),
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
        LATEST_THUNDERBIRD_VERSION=get_latest_version(
            releases,
            shipit_api.config.THUNDERBIRD_RELEASE_BRANCH,
            Product.THUNDERBIRD),
        LATEST_THUNDERBIRD_DEVEL_VERSION=get_latest_version(
            releases,
            shipit_api.config.THUNDERBIRD_BETA_BRANCH,
            Product.THUNDERBIRD),
        LATEST_THUNDERBIRD_NIGHTLY_VERSION=shipit_api.config.LATEST_THUNDERBIRD_NIGHTLY_VERSION,
        LATEST_THUNDERBIRD_ALPHA_VERSION=shipit_api.config.LATEST_THUNDERBIRD_ALPHA_VERSION,
    )


def get_thunderbird_beta_builds(old_product_details: ProductDetails) -> typing.Dict:
    '''This file is empty and not used today.

       This function will output to the following files:
        - thunderbird_beta_builds.json

       Example:::

           {}
    '''
    return dict()


@click.command(name='upload-product-details')
@click.option(
    '--data-dir',
    required=True,
    type=click.Path(
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
    ),
)
@click.option(
    '--s3-bucket',
    required=True,
    type=str,
    )
@click.option(
    '--aws-access-key-id',
    required=True,
    type=str,
    )
@click.option(
    '--aws-secret-access-key',
    required=True,
    type=str,
    )
@click.option(
    '--breakpoint-version',
    default=shipit_api.config.BREAKPOINT_VERSION,
    type=int,
)
@click.option(
    '-K',
    '--keep-temporary-dir',
    is_flag=True,
)
@flask.cli.with_appcontext
def upload_product_details(data_dir: str,
                           s3_bucket: str,
                           aws_access_key_id: str,
                           aws_secret_access_key: str,
                           breakpoint_version: int,
                           keep_temporary_dir: bool):

    # get data from older product-details
    old_product_details = get_old_product_details(data_dir)

    # get all the releases from the database from (including)
    # breakpoint_version on
    releases = get_releases_from_db(flask.current_app.db.session, breakpoint_version)
    all_releases = get_releases_from_db(flask.current_app.db.session)

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
                                                          old_product_details,
                                                          ),
        'firefox_versions.json': get_firefox_versions(releases),
        'languages.json': get_languages(old_product_details),
        'mobile_android.json': get_releases(breakpoint_version,
                                            [Product.FENNEC],
                                            releases,
                                            old_product_details,
                                            ),
        'mobile_details.json': get_mobile_details(old_product_details),
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
        'thunderbird_beta_builds.json': get_thunderbird_beta_builds(old_product_details),
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
                                                              old_product_details,
                                                              ),
        'thunderbird_versions.json': get_thunderbird_versions(releases),
    }
    product_details.update(get_regions(old_product_details))
    product_details.update(get_l10n(all_releases, releases, old_product_details))

    #  add 'json/1.0/' infront of each file path
    product_details = {
        f'json/1.0{file_}': content
        for file_, content in product_details.items()
    }

    # create json_exports.json to list all the files
    product_details['json_exports.json'] = {
        file_: os.path.basename(file_)
        for file_ in product_details.keys()
    }

    # create temp directory where generated files will be temporary created
    temp_dir_ = tempfile.mkdtemp(prefix='product-details-')
    try:
        temp_dir = pathlib.Path(temp_dir_)

        for (file__, content) in product_details.items():
            file_ = temp_dir / file__

            # we must ensure that all needed folders exists
            if file_.parent != temp_dir:
                os.makedirs(str(file_.parent))

            # write content into json file
            with file_.open('w+') as f:
                f.write(json.dumps(content, sort_keys=True, indent=4))

        # sync to s3 make it atomic or close
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
        aws = awscli.clidriver.create_clidriver().main
        returncode = aws([
            's3',
            'sync',
            '--quiet',
            '--delete',
            temp_dir.absolute().as_posix(),
            's3://' + s3_bucket,
        ])

        if returncode == 0:
            click.secho(f'Successfully synced product details to {s3_bucket} S3 bucket.', fg='green')
        else:
            click.secho(f'Failed syncing product details to {s3_bucket} S3 bucket.', fg='red')

    finally:
        if keep_temporary_dir:
            click.echo(f'Temporary folder: {temp_dir}')
        else:
            shutil.rmtree(temp_dir)


def get_taskcluster_headers(request_url,
                            method,
                            content,
                            taskcluster_client_id,
                            taskcluster_access_token,
                            ):
    hawk = mohawk.Sender(
        {
            'id': taskcluster_client_id,
            'key': taskcluster_access_token,
            'algorithm': 'sha256',
        },
        request_url,
        method,
        content,
        content_type='application/json',
    )
    return {
        'Authorization': hawk.request_header,
        'Content-Type': 'application/json',
    }


@click.command(name='shipit-v1-sync')
@click.option(
    '--ldap-username',
    help='LDAP username',
    required=True,
    prompt=True,
)
@click.option(
    '--ldap-password',
    help='LDAP password',
    required=True,
    prompt=True,
    hide_input=True,
)
@click.option(
    '--taskcluster-client-id',
    help='Taskcluster Client ID',
    required=True,
    prompt=True,
)
@click.option(
    '--taskcluster-access-token',
    help='Taskcluster Access token',
    required=True,
    prompt=True,
    hide_input=True,
)
@click.option(
    '--api-from',
    default='https://ship-it.mozilla.org',
)
@click.option(
    '--api-to',
    required=True,
)
def shipit_v1_sync(ldap_username,
                   ldap_password,
                   taskcluster_client_id,
                   taskcluster_access_token,
                   api_from,
                   api_to,
                   ):

    s = requests.Session()
    s.auth = (ldap_username, ldap_password)

    click.echo('Fetching release list...', nl=False)
    req = s.get(f'{api_from}/releases')
    releases = req.json()['releases']
    click.echo(click.style('OK', fg='green'))

    releases_json = []

    with click.progressbar(releases, label='Fetching release data') as releases:
        for release in releases:
            r = s.get(f'{api_from}/releases/{release}')
            releases_json.append(r.json())

    click.echo('Syncing release list...', nl=False)
    headers = get_taskcluster_headers(
        f'{api_to}/sync',
        'post',
        json.dumps(releases_json),
        taskcluster_client_id,
        taskcluster_access_token,
    )
    r = requests.post(
        f'{api_to}/sync',
        headers=headers,
        verify=False,
        json=releases_json,
    )
    r.raise_for_status()
    click.echo(click.style('OK', fg='green'))
