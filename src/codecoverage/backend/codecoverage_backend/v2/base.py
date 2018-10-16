# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from elasticsearch import Elasticsearch

from cli_common import log
from codecoverage_backend import secrets
from codecoverage_backend.datadog import get_stats
from codecoverage_backend.services.active_data import ActiveDataCoverage

logger = log.get_logger(__name__)
stats = get_stats()


class NoResults(Exception):
    '''
    Raised when no results were found
    '''


class ActiveData(object):
    '''
    API v2 ActiveData synchronous client, sharing common queries
    '''
    client = None

    def __init__(self):
        try:
            conf = secrets.ACTIVE_DATA
            self.client = Elasticsearch(
                hosts=[conf['url'], ],
                http_auth=(
                    conf['user'],
                    conf['password'],
                )
            )
        except Exception as e:
            logger.warn('ES client failure: {}'.format(e))

    def search(self, name, body, timeout=10):
        with stats.timer('active_data.{}'.format(name)):
            out = self.client.search(
                index=secrets.ACTIVE_DATA_INDEX,
                body=body,
                request_timeout=timeout,
            )
        if out is None:
            raise Exception('No response from ES server')
        if out['timed_out']:
            logger.warn('ES query {} timed out'.format(name))
        else:
            logger.info('ES query {name} took {time}s to hit {nb} items'.format(
                name=name,
                time=out['took'] / 1000.0,
                nb=out['hits'].get('total', 0),
                scroll='1m',
            ))
        if out['hits']['total'] == 0:
            raise NoResults
        return out

    @property
    def enabled(self):
        return self.client is not None

    @stats.timed('active_data.get_latest_changeset')
    def get_latest_changeset(self):
        '''
        Get the latest coverage changeset pushed to ES
        '''
        query = ActiveDataCoverage.available_revisions_query(nb=1)
        out = self.search('latest-build', query, timeout=30)
        if out['aggregations']:
            return out['aggregations']['revisions']['buckets'][0]['key']


# Shared instance
active_data = ActiveData()
