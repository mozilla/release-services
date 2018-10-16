# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

import datadog

from codecoverage_backend import config
from codecoverage_backend import secrets

logger = logging.getLogger(__name__)

__stats = None


def get_stats():
    '''
    Configure a shared ThreadStats instance for datadog
    '''
    global __stats

    if __stats is not None:
        return __stats

    if secrets.DATADOG_API_KEY:
        datadog.initialize(
            api_key=secrets.DATADOG_API_KEY,
            host_name='coverage.{}.moz.tools'.format(secrets.APP_CHANNEL),
        )
    else:
        logger.info('No datadog credentials')

    # Must be instantiated after initialize
    # https://datadogpy.readthedocs.io/en/latest/#datadog-threadstats-module
    __stats = datadog.ThreadStats(
        constant_tags=[
            config.PROJECT_NAME,
            'channel:{}'.format(secrets.APP_CHANNEL),
        ],
    )
    __stats.start(flush_in_thread=True)
    return __stats
