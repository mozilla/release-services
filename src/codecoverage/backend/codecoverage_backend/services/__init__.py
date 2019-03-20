# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cli_common import log
from codecoverage_backend import secrets
from codecoverage_backend.services import active_data
from codecoverage_backend.services import codecov
from codecoverage_backend.services import coveralls

logger = log.get_logger(__name__)


def build_coverage_service():
    '''
    Instanciate coverage service from TC secret
    '''
    services = {
        'codecov': codecov.CodecovCoverage,
        'coveralls': coveralls.CoverallsCoverage,
        'activedata': active_data.ActiveDataCoverage,
    }
    if secrets.COVERAGE_SERVICE not in services:
        raise Exception('Unknown coverage service : {}'.format(secrets.COVERAGE_SERVICE))

    service = services[secrets.COVERAGE_SERVICE]()
    logger.info('Using coverage service', service=service)
    return service


coverage_service = build_coverage_service()
