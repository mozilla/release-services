# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pathlib
import tempfile

PROJECT_NAME = 'shipit/api'
APP_NAME = 'shipit_api'
SCOPE_PREFIX = f'project:releng:services/{APP_NAME}'

# A route key that triggers rebuild of product details.
# Worker will listen to this route key to trigger the rebuild.
PULSE_ROUTE_REBUILD_PRODUCT_DETAILS = 'rebuild_product_details'

# A folder where we will keep a checkout of product details
PRODUCT_DETAILS_DIR = pathlib.Path(tempfile.gettempdir(), 'product-details')
PRODUCT_DETAILS_NEW_DIR = pathlib.Path(tempfile.gettempdir(), 'product-details-new')
PRODUCT_DETAILS_CACHE_DIR = pathlib.Path(tempfile.gettempdir(), 'product-details-cache')

BREAKPOINT_VERSION = 60

# When there is only one ESR release ESR_NEXT is set to '' and ESR_CURRENT is
# set to current ESR major version.  When we have 2 ESR releases, ESR_CURRENT
# should be using the major version of the older release, while ESR_NEXT should
# be using the major version of the release with greater version.
CURRENT_ESR = '60'
ESR_NEXT = ''
# Pre Firefox version
LATEST_FIREFOX_OLDER_VERSION = '3.6.28'
# TODO: move the branch configs to secrets
RELEASE_BRANCH = 'releases/mozilla-release'
BETA_BRANCH = 'releases/mozilla-beta'
ESR_BRANCH_PREFIX = 'releases/mozilla-esr'
# FIREFOX_NIGHTLY version is hard coded and requires a human to update it after
# the latest Nightly builds are available on CDNs after version bump (merge
# day).
# We could have used the in-tree version, but there can be race conditions,
# e.g. version bumped, but still no builds available.
FIREFOX_NIGHTLY = '70.0a1'
FENNEC_NIGHTLY = '68.1a1'
# The next 6 dates are information about the current and next release
# They must be updated at the same time as FIREFOX_NIGHTLY
# They can be found: https://wiki.mozilla.org/Release_Management/Calendar
LAST_SOFTFREEZE_DATE = '2019-07-01'
LAST_MERGE_DATE = '2019-07-08'
LAST_RELEASE_DATE = '2019-07-09'
NEXT_SOFTFREEZE_DATE = '2019-08-26'
NEXT_MERGE_DATE = '2019-09-02'
NEXT_RELEASE_DATE = '2019-09-03'

# Aurora has been replaced by Dev Edition, but some 3rd party applications may
# still rely on this value.
FIREFOX_AURORA = ''

# IOS versions
IOS_BETA_VERSION = ''
IOS_VERSION = '12.1'

# Thunderbird configs
LATEST_THUNDERBIRD_ALPHA_VERSION = '54.0a2'
LATEST_THUNDERBIRD_NIGHTLY_VERSION = '69.0a1'
# TODO: Need to update this every cycle?
THUNDERBIRD_RELEASE_BRANCH = 'releases/comm-esr60'
THUNDERBIRD_BETA_BRANCH = 'releases/comm-beta'

# Mixed
HG_PREFIX = 'https://hg.mozilla.org'

MOBILE_DETAILS_TEMPLATE = r'''
{
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
        {
            "locale": {
                "code": "ca",
                "english": "Catalan",
                "native": "Catal\u00e0"
            }
        },
        {
            "locale": {
                "code": "cs",
                "english": "Czech",
                "native": "\u010ce\u0161tina"
            }
        },
        {
            "locale": {
                "code": "de",
                "english": "German",
                "native": "Deutsch"
            }
        },
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            }
        },
        {
            "locale": {
                "code": "es-AR",
                "english": "Spanish (Argentina)",
                "native": "Espa\u00f1ol (de Argentina)"
            }
        },
        {
            "locale": {
                "code": "es-ES",
                "english": "Spanish (Spain)",
                "native": "Espa\u00f1ol (de Espa\u00f1a)"
            }
        },
        {
            "locale": {
                "code": "eu",
                "english": "Basque",
                "native": "Euskara"
            }
        },
        {
            "locale": {
                "code": "fa",
                "english": "Persian",
                "native": "\u0641\u0627\u0631\u0633\u06cc"
            }
        },
        {
            "locale": {
                "code": "fi",
                "english": "Finnish",
                "native": "suomi"
            }
        },
        {
            "locale": {
                "code": "fr",
                "english": "French",
                "native": "Fran\u00e7ais"
            }
        },
        {
            "locale": {
                "code": "fy-NL",
                "english": "Frisian",
                "native": "Frysk"
            }
        },
        {
            "locale": {
                "code": "ga-IE",
                "english": "Irish",
                "native": "Gaeilge"
            }
        },
        {
            "locale": {
                "code": "gl",
                "english": "Galician",
                "native": "Galego"
            }
        },
        {
            "locale": {
                "code": "hu",
                "english": "Hungarian",
                "native": "magyar"
            }
        },
        {
            "locale": {
                "code": "it",
                "english": "Italian",
                "native": "Italiano"
            }
        },
        {
            "locale": {
                "code": "ja",
                "english": "Japanese",
                "native": "\u65e5\u672c\u8a9e"
            }
        },
        {
            "locale": {
                "code": "lt",
                "english": "Lithuanian",
                "native": "lietuvi\u0173 kalba"
            }
        },
        {
            "locale": {
                "code": "nl",
                "english": "Dutch",
                "native": "Nederlands"
            }
        },
        {
            "locale": {
                "code": "pa-IN",
                "english": "Punjabi (India)",
                "native": "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40 (\u0a2d\u0a3e\u0a30\u0a24)"
            }
        },
        {
            "locale": {
                "code": "pl",
                "english": "Polish",
                "native": "Polski"
            }
        },
        {
            "locale": {
                "code": "pt-BR",
                "english": "Portuguese (Brazilian)",
                "native": "Portugu\u00eas (do\u00a0Brasil)"
            }
        },
        {
            "locale": {
                "code": "pt-PT",
                "english": "Portuguese (Portugal)",
                "native": "Portugu\u00eas (Europeu)"
            }
        },
        {
            "locale": {
                "code": "ro",
                "english": "Romanian",
                "native": "Rom\u00e2n\u0103"
            }
        },
        {
            "locale": {
                "code": "ru",
                "english": "Russian",
                "native": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439"
            }
        },
        {
            "locale": {
                "code": "sk",
                "english": "Slovak",
                "native": "sloven\u010dina"
            }
        },
        {
            "locale": {
                "code": "tr",
                "english": "Turkish",
                "native": "T\u00fcrk\u00e7e"
            }
        },
        {
            "locale": {
                "code": "uk",
                "english": "Ukrainian",
                "native": "\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430"
            }
        },
        {
            "locale": {
                "code": "zh-CN",
                "english": "Chinese (Simplified)",
                "native": "\u4e2d\u6587 (\u7b80\u4f53)"
            }
        },
        {
            "locale": {
                "code": "zh-TW",
                "english": "Chinese (Traditional)",
                "native": "\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)"
            }
        }
    ],
    "beta_builds": [
        {
            "locale": {
                "code": "cs",
                "english": "Czech",
                "native": "\u010ce\u0161tina"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "de",
                "english": "German",
                "native": "Deutsch"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "es-ES",
                "english": "Spanish (Spain)",
                "native": "Espa\u00f1ol (de Espa\u00f1a)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "fi",
                "english": "Finnish",
                "native": "suomi"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "fr",
                "english": "French",
                "native": "Fran\u00e7ais"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "it",
                "english": "Italian",
                "native": "Italiano"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "ja",
                "english": "Japanese",
                "native": "\u65e5\u672c\u8a9e"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "nl",
                "english": "Dutch",
                "native": "Nederlands"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "pl",
                "english": "Polish",
                "native": "Polski"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "pt-PT",
                "english": "Portuguese (Portugal)",
                "native": "Portugu\u00eas (Europeu)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        },
        {
            "locale": {
                "code": "ru",
                "english": "Russian",
                "native": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox_beta"
            }
        }
    ],
    "alpha_builds": [
        {
            "locale": {
                "code": "en-US",
                "english": "English (US)",
                "native": "English (US)"
            },
            "download": {
                "android": "market:\/\/details?id=org.mozilla.firefox"
            }
        }
    ]
}
'''

# Phases per product, ordered
SUPPORTED_FLAVORS = {
    'firefox': [
        {'name': 'promote_firefox', 'in_previous_graph_ids': True},
        {'name': 'push_firefox', 'in_previous_graph_ids': True},
        {'name': 'ship_firefox', 'in_previous_graph_ids': True},
    ],
    'firefox_rc': [
        {'name': 'promote_firefox_rc', 'in_previous_graph_ids': True},
        {'name': 'ship_firefox_rc', 'in_previous_graph_ids': False},
        {'name': 'push_firefox', 'in_previous_graph_ids': True},
        {'name': 'ship_firefox', 'in_previous_graph_ids': True},
    ],
    'fennec': [
        {'name': 'promote_fennec', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec', 'in_previous_graph_ids': True},
    ],
    'fennec_rc': [
        {'name': 'promote_fennec', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec_rc', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec', 'in_previous_graph_ids': True},
    ],
    'devedition': [
        {'name': 'promote_devedition', 'in_previous_graph_ids': True},
        {'name': 'push_devedition', 'in_previous_graph_ids': True},
        {'name': 'ship_devedition', 'in_previous_graph_ids': True},
    ],
    'thunderbird': [
        {'name': 'promote_thunderbird', 'in_previous_graph_ids': True},
        {'name': 'push_thunderbird', 'in_previous_graph_ids': True},
        {'name': 'ship_thunderbird', 'in_previous_graph_ids': True},
    ],
    'fennec_beta': [
        {'name': 'promote_fennec_beta', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec_beta', 'in_previous_graph_ids': True},
    ],
    'fennec_release': [
        {'name': 'promote_fennec_release', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec_release', 'in_previous_graph_ids': True},
    ],
    'fennec_release_rc': [
        {'name': 'promote_fennec_release', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec_release_rc', 'in_previous_graph_ids': True},
        {'name': 'ship_fennec_release', 'in_previous_graph_ids': True},
    ],
}

# TODO: add other branches
# TODO: consider move this to secrets, aka per env config
SIGNOFFS = {
    # 'projects/maple': {
    #     'fennec': {
    #         'ship_fennec': [
    #             {
    #                 'name': '[relman] Ship Fennec',
    #                 'description': 'Publish Firefox for Android to Play Store',
    #                 # TODO: this group includes releng/relman/qa/etc, need to split or switch to real scopes
    #                 'permissions': 'vpn_cloudops_shipit',
    #             },
    #             {
    #                 'name': '[releng] Ship Fennec',
    #                 'description': 'Publish Firefox for Android to Play Store',
    #                 # XXX: stands for the LDAP group for now
    #                 'permissions': 'releng',
    #             },
    #         ],
    #     },
    # },
}
