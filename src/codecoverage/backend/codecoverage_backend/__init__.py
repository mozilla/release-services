# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

import codecoverage_backend.config
import codecoverage_backend.datadog
import codecoverage_backend.services.gcp
from cli_common import log

logger = log.get_logger(__name__)


def create_app(config=None):
    import backend_common

    app = backend_common.create_app(
        project_name=codecoverage_backend.config.PROJECT_NAME,
        app_name=codecoverage_backend.config.APP_NAME,
        config=config,
        extensions=[
            'log',
            'security',
            'cors',
            'api',
        ],
    )
    # TODO: add predefined api.yml
    app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))

    # Setup datadog stats
    codecoverage_backend.datadog.get_stats()

    # Warm up GCP cache
    try:
        codecoverage_backend.services.gcp.load_cache()
    except Exception as e:
        logger.warn('GCP cache warmup failed: {}'.format(e))

    return app
