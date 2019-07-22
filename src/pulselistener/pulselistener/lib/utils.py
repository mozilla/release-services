# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time

import structlog

log = structlog.get_logger(__name__)


class RunException(Exception):
    '''
    Exception used to stop retrying
    '''


def retry(operation,
          retries=5,
          wait_between_retries=30,
          exception_to_break=RunException,
          ):
    while True:
        try:
            return operation()
        except Exception as e:
            if isinstance(e, exception_to_break):
                raise
            retries -= 1
            if retries == 0:
                raise
            time.sleep(wait_between_retries)
