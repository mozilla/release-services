# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from cli_common import log
from shipit_static_analysis.report.base import Reporter

logger = log.get_logger(__name__)


class PhabricatorReporter(Reporter):
    '''
    API connector to report on Phabricator
    '''
    def __init__(self, configuration, *args):
        url, api_key = self.requires(configuration, 'url', 'api_key')

    def publish(self, issues, review_request_id, diffset_revision, diff_url):
        '''
        Send an email to administrators
        '''
