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
import shutil
import tempfile
import typing

import aiohttp
import click
import mypy_extensions
import typeguard


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


ReleaseDetails = mypy_extensions.TypedDict('ReleaseDetails', {
    'category': str,
    'product': str,
    'build_number': int,
    'description': str,
    'is_security_driven': bool,
    'version': str,
    'date': str,
})
Releases = typing.Dict[str, ReleaseDetails]
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
Regions = typing.Dict[str, str]
ThunderbirdVersions = mypy_extensions.TypedDict('ThunderbirdVersions', {
    'LATEST_THUNDERBIRD_VERSION': str,
    'LATEST_THUNDERBIRD_ALPHA_VERSION': str,
    'LATEST_THUNDERBIRD_DEVEL_VERSION': str,
    'LATEST_THUNDERBIRD_NIGHTLY_VERSION': str,
})

File = str
JSONDict = typing.Dict
ProductDetails = typing.Dict[File, JSONDict]
Products = typing.List[Product]


@typeguard.typechecked
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


@typeguard.typechecked
def get_releases(products: Products, old_product_details: ProductDetails) -> Releases:
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
    return dict()  # TODO: not implemented


@typeguard.typechecked
def get_release_history(product: Product,
                        product_category: ProductCategory,
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
    return dict()  # TODO: not implemented


@typeguard.typechecked
def get_primary_builds(product: Product,
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
    return dict()  # TODO: not implemented


@typeguard.typechecked
def get_firefox_versions(old_product_details: ProductDetails) -> FirefoxVersions:
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
        FIREFOX_NIGHTLY='',
        FIREFOX_AURORA='',
        FIREFOX_ESR_NEXT='',
        LATEST_FIREFOX_DEVEL_VERSION='',
        FIREFOX_DEVEDITION='',
        LATEST_FIREFOX_OLDER_VERSION='',
        LATEST_FIREFOX_RELEASED_DEVEL_VERSION='',
        LATEST_FIREFOX_VERSION='',
    )


@typeguard.typechecked
def get_regions(old_product_details: ProductDetails) -> typing.Dict[File, Regions]:
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
    return {
        file_: content
        for file_, content in old_product_details.items()
        if file_.startswith('json/1.0/regions/')
    }


@typeguard.typechecked
def get_l10n(old_product_details: ProductDetails) -> typing.Dict[File, L10n]:
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
    return dict()


@typeguard.typechecked
def get_languages(old_product_details: ProductDetails) -> typing.Dict[str, Languages]:
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
    file_ = 'json/1.0/languages.json'
    data = dict()
    if file_ in old_product_details:
        data[file_] = old_product_details[file_]
    return data


@typeguard.typechecked
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


@typeguard.typechecked
def get_mobile_versions(old_product_details: ProductDetails) -> MobileVersions:
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


@typeguard.typechecked
def get_thunderbird_versions(old_product_details: ProductDetails) -> ThunderbirdVersions:
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
        LATEST_THUNDERBIRD_VERSION='52.6.0',
        LATEST_THUNDERBIRD_ALPHA_VERSION='54.0a2',
        LATEST_THUNDERBIRD_DEVEL_VERSION='59.0b2',
        LATEST_THUNDERBIRD_NIGHTLY_VERSION='60.0a1',
    )


@typeguard.typechecked
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
    '--keep-temporary-dir',
    is_flag=True,
)
def upload_product_details(data_dir: str, keep_temporary_dir: bool):

    # get data from older product-details
    old_product_details = get_old_product_details(data_dir)

    # TODO: we should do all IO here

    # combine old and new data
    product_details: ProductDetails = {
        file_: method(old_product_details)
        for file_, method in [
            ('all.json', functools.partial(get_releases, [i.value for i in list(Product)])),
            ('devedition.json', functools.partial(get_releases, [Product.DEVEDITION])),
            ('firefox.json', functools.partial(get_releases, [Product.FIREFOX])),
            ('firefox_history_development_releases.json', functools.partial(get_release_history, Product.FIREFOX, ProductCategory.DEVELOPMENT)),
            ('firefox_history_major_releases.json', functools.partial(get_release_history, Product.FIREFOX, ProductCategory.MAJOR)),
            ('firefox_history_stability_releases.json', functools.partial(get_release_history, Product.FIREFOX, ProductCategory.STABILITY)),
            ('firefox_primary_builds.json', functools.partial(get_primary_builds, Product.FIREFOX)),
            ('firefox_versions.json', get_firefox_versions),
            ('languages.json', get_languages),
            ('mobile_android.json', functools.partial(get_releases, [Product.FENNEC])),
            ('mobile_details.json', get_mobile_details),
            ('mobile_history_development_releases.json', functools.partial(get_release_history, Product.FENNEC, ProductCategory.DEVELOPMENT)),
            ('mobile_history_major_releases.json', functools.partial(get_release_history, Product.FENNEC, ProductCategory.MAJOR)),
            ('mobile_history_stability_releases.json', functools.partial(get_release_history, Product.FENNEC, ProductCategory.STABILITY)),
            ('mobile_versions.json', get_mobile_versions),
            ('thunderbird.json', functools.partial(get_releases, [Product.THUNDERBIRD])),
            ('thunderbird_beta_builds.json', get_thunderbird_beta_builds),
            ('thunderbird_history_development_releases.json', functools.partial(get_release_history, Product.THUNDERBIRD, ProductCategory.DEVELOPMENT)),
            ('thunderbird_history_major_releases.json', functools.partial(get_release_history, Product.THUNDERBIRD, ProductCategory.MAJOR)),
            ('thunderbird_history_stability_releases.json', functools.partial(get_release_history, Product.THUNDERBIRD, ProductCategory.STABILITY)),
            ('thunderbird_primary_builds.json', functools.partial(get_primary_builds, Product.THUNDERBIRD)),
            ('thunderbird_versions.json', get_thunderbird_versions),
        ]
    }
    product_details.update(get_regions(old_product_details))
    product_details.update(get_l10n(old_product_details))

    # TODO: json_exports.json

    # create temp directory where generated files will be temporary created
    temp_dir_ = tempfile.mkdtemp(prefix='product-details-')
    try:
        temp_dir = pathlib.Path(temp_dir_)

        for (file__, content) in product_details.items():
            file_ = temp_dir / file__

            # we must ensure that all needed folders exists
            os.makedirs(str(file_.parent))

            # write content into json file
            with file_.open('w+') as f:
                f.write(json.dumps(content, sort_keys=True, indent=4))

        # TODO: sync to s3

    finally:
        if keep_temporary_dir:
            click.echo(f'Temporary folder: {temp_dir}')
        else:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    upload_product_details()
