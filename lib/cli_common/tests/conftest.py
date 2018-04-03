# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logbook
import pytest


@pytest.fixture(scope='module')
def logger():
    '''
    Build a logger
    '''

    import cli_common.log

    cli_common.log.init_logger('cli_common', level=logbook.DEBUG)
    return cli_common.log.get_logger(__name__)
