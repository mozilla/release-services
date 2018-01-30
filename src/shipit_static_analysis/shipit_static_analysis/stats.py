from __future__ import absolute_import
from shipit_static_analysis.config import settings
import datadog


class Datadog(object):
    '''
    Log metrics using Datadog REST api
    '''

    def auth(self, datadog_token):
        datadog.initialize(
            api_key=datadog_token,
            host_name='dev',
        )
        self.api = datadog.ThreadStats(
            constant_tags=[settings.app_channel, ],
        )
        self.api.start()

    def increment(self, metric, value=1):
        self.api.increment(
            metric,
            value=value,
        )

    def stop(self):
        print('flushing')
        self.api.flush()
        self.api.stop()

    def report_issues(self, name, issues):
        '''
        Aggregate statistics about found issues
        '''

        # Report all issues found
        self.increment(
            'issues.{}'.format(name),
            len(issues),
        )

        # Report publishable issues
        self.increment(
            'issues.{}.publishable'.format(name),
            sum([i.is_publishable() for i in issues]),
        )
