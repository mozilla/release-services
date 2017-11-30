# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


class Reporter(object):
    '''
    Common interface to post reports on a website
    Will configure & build reports
    '''
    def __init__(self, configuration, client_id, access_token):
        '''
        Configure reporter using Taskcluster credentials and configuration
        '''
        raise NotImplementedError

    def publish(self, issues, revision, diff_url):
        '''
        Publish a new report
        '''
        raise NotImplementedError

    def requires(self, configuration, *keys):
        '''
        Check all configuration necessary keys are present
        '''
        assert isinstance(configuration, dict)

        out = []
        for key in keys:
            assert key in configuration, \
                'Missing {} {}'.format(self.__class__.__name__, key)
            out.append(configuration[key])

        return out
