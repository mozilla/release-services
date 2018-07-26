# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from elasticsearch import Elasticsearch
from esFrontLine.client.sync import HawkConnection

from cli_common import log
from shipit_code_coverage_backend import secrets
from shipit_code_coverage_backend.services.active_data import ActiveDataCoverage

logger = log.get_logger(__name__)


INDEX_COVERAGE = 'coverage'
INDEX_REPO = 'repo'

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
            self.client = Elasticsearch(
                hosts=[secrets.ESFRONTLINE['url']],
                connection_class=HawkConnection,
                hawk_credentials=secrets.ESFRONTLINE['user'],
            )
        except Exception as e:
            logger.warn('ES client failure: {}'.format(e))

    def search(self, name, body, timeout=10, index=INDEX_COVERAGE):
        out = self.client.search(
            index=index,
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

    def get_latest_changeset(self):
        '''
        Get the latest coverage changeset pushed to ES
        '''
        query = ActiveDataCoverage.available_revisions_query(nb=1)
        out = self.search('latest-build', query)
        if out['aggregations']:
            return out['aggregations']['revisions']['buckets'][0]['key']

    def get_changeset(self, changeset, repository='mozilla-central'):
        '''
        Load changeset data from a repository, with push, desc, bugzilla_id, files
        '''
        query = {
            'query': {
                'bool': {
                    'must': [
                        {'match': {'changeset.id': changeset}},
                        {'match': {'branch.name': repository}},
                    ]
                }
            }
        }
        out = self.search('changeset-coverage', query, index=INDEX_REPO)
        assert out['hits']['total'] == 1, \
            'Too many items found for {}'.format(changeset)

        return out['hits']['hits'][0]['_source']

# Shared instance
active_data = ActiveData()
