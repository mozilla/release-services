# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cli_common import log
from codecoverage_backend.services import codecov

logger = log.get_logger(__name__)


# Only support codecov for legacy endpoints
coverage_service = codecov.CodecovCoverage()
