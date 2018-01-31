# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from shipit_static_analysis.config import settings
import datadog


class Datadog(object):
    '''
    Log metrics using Datadog REST api
    '''
    api = None

    def auth(self, api_key, app_key=None):
        datadog.initialize(
            api_key=api_key,
            app_key=app_key,
            host_name='{}.code-review'.format(settings.app_channel),
        )
        self.api = datadog.ThreadStats(
            constant_tags=[settings.app_channel, ],
        )
        self.api.start()

    def report_issues(self, name, issues):
        '''
        Aggregate statistics about found issues
        '''
        if self.api is None:
            return

        # Report all issues found
        self.api.increment(
            'issues.{}'.format(name),
            len(issues),
        )

        # Report publishable issues
        self.api.increment(
            'issues.{}.publishable'.format(name),
            sum([i.is_publishable() for i in issues]),
        )
