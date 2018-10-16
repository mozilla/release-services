# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import inspect
import itertools
import time

from async_lru import alru_cache
from elasticsearch_async import AsyncElasticsearch

from cli_common import log
from codecoverage_backend import secrets
from codecoverage_backend.datadog import get_stats
from codecoverage_backend.services.base import Coverage

logger = log.get_logger(__name__)
stats = get_stats()


class TookCounter(AsyncElasticsearch):
    '''
    Overrides elasticsearch client to count the time took and
    reported by ES server
    '''
    took = 0

    async def search(self, *args, **kwargs):
        return self._save_took(await super().search(*args, **kwargs))

    async def count(self, *args, **kwargs):
        return self._save_took(await super().count(*args, **kwargs))

    def _save_took(self, data):
        if isinstance(data, dict) and 'took' in data:
            self.took += data['took'] / 1000.0  # took is in ms

        return data


class ActiveDataClient():
    '''
    Active data async client, through Elastic Search
    '''

    def __init__(self):
        self.start_time = None
        conf = secrets.ACTIVE_DATA
        self.client = TookCounter(
            hosts=[conf['url'], ],
            http_auth=(
                conf['user'],
                conf['password'],
            )
        )

        # Use name from the calling function in the stack
        stack = inspect.stack()
        self.name = stack[1].function if len(stack) > 1 else 'unknown'

    async def __aenter__(self):
        self.start_time = time.time()
        return self.client

    async def __aexit__(self, *args, **kwargs):

        # Report full query time in datadog
        if self.start_time is not None:
            query_time = time.time() - self.start_time
            stats.histogram('codecoverage.active_data.{}'.format(self.name), query_time)
            logger.info('ActiveData full query {} took {:0.2f}s'.format(self.name, query_time))

        # Report ES query time in datadog
        if self.client.took > 0:
            stats.histogram('codecoverage.active_data.es.{}'.format(self.name), self.client.took)
            logger.info('ActiveData ES query {} took {:0.2f}s'.format(self.name, self.client.took))

        await self.client.transport.close()


class ActiveDataCoverage(Coverage):

    FIELD_REPO = 'repo.branch.name.~s~'
    FIELD_FILENAME = 'source.file.name.~s~'
    FIELD_CHANGESET = 'repo.changeset.id.~s~'
    FIELD_CHANGESET_DATE = 'repo.changeset.date.~n~'
    FIELD_TOTAL_PERCENT = 'source.file.percentage_covered.~n~'
    FIELD_TEST_SUITE = 'test.suite.~s~'
    FIELD_BUILD_TYPE = 'build.type.~s~'
    FIELD_RUN_NAME = 'run.name.~s~'

    @staticmethod
    def base_query(filters=[], excludes=[]):
        '''
        Build an ElasticSearch base query used for all more complex ones
        '''
        base_filters = [
            # Always query on Mozilla Central
            {'term': {ActiveDataCoverage.FIELD_REPO: 'mozilla-central'}},
        ]

        base_excludes = [
            # Ignore awsy and talos suites
            {'term': {ActiveDataCoverage.FIELD_TEST_SUITE: 'awsy'}},
            {'term': {ActiveDataCoverage.FIELD_TEST_SUITE: 'talos'}},

            # Ignore jsdcov builds
            {'term': {ActiveDataCoverage.FIELD_BUILD_TYPE: 'jsdcov'}},

            # Ignore per-test suites by disabling debug-test runs
            {'wildcard': {ActiveDataCoverage.FIELD_RUN_NAME: 'test-*/debug-test-coverage-*'}},

            # Ignore obj-firefox/*
            {'prefix': {ActiveDataCoverage.FIELD_FILENAME: 'obj-firefox/'}},
        ]

        return {
            'query': {
                'bool': {
                    'must': base_filters + filters,
                    'must_not': base_excludes + excludes,
                }
            }
        }

    @staticmethod
    async def list_tests(changeset, filename):
        '''
        List all the tests available for file in a changeset
        '''
        query = ActiveDataCoverage.base_query(
            filters=[
                # Filter by filename and changeset
                {'term': {ActiveDataCoverage.FIELD_FILENAME: filename}},
                {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
            ]
        )

        async with ActiveDataClient() as es:
            # First, count results
            res = await es.count(index=secrets.ACTIVE_DATA_INDEX, body=query)
            count = res['count']

            # Load available results
            if count > 0:
                # TODO: support pagination / scroll ?
                tests = await es.search(index=secrets.ACTIVE_DATA_INDEX, body=query)
                return count, tests['hits']['hits']

        return count, []

    @staticmethod
    def available_revisions_query(nb=2, max_date=None):
        '''
        Search the N last revisions available in the ES cluster
        '''

        # Limit search to a maximum date
        filters = []
        if max_date:
            filters.append({
                'range': {
                    ActiveDataCoverage.FIELD_CHANGESET_DATE: {
                        'lt': max_date,
                    },
                },
            })

        query = ActiveDataCoverage.base_query(filters)
        query.update({
            # no search results please
            'size': 0,

            'aggs': {
                'revisions': {
                    'terms': {
                        # List changeset ids, sorted by changeset_date
                        'field': ActiveDataCoverage.FIELD_CHANGESET,
                        'order': {'_date': 'desc'},
                        'size': nb,
                    },

                    'aggs': {
                        # Calc average changeset date per bucket (as timestamp)
                        '_date': {
                            'avg': {
                                'field': ActiveDataCoverage.FIELD_CHANGESET_DATE,
                                'missing': 0,
                            },
                        }
                    },
                },
            },
        })
        return query

    @staticmethod
    async def available_revisions(nb=2, max_date=None):
        async with ActiveDataClient() as es:
            out = await es.search(
                index=secrets.ACTIVE_DATA_INDEX,
                body=ActiveDataCoverage.available_revisions_query(nb, max_date),

                # Longer timeout, the sub aggregation is long
                request_timeout=30,
            )
            return out['aggregations']['revisions']['buckets']

    @staticmethod
    async def get_revision_date(changeset):
        '''
        Get the date of a revision
        '''
        query = ActiveDataCoverage.base_query([
            {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
        ])
        query.update({
            # no search results please
            'size': 0,

            'aggs': {
                'date': {
                    'avg': {
                        'field': ActiveDataCoverage.FIELD_CHANGESET_DATE,
                    },
                },
            },
        })
        async with ActiveDataClient() as es:
            out = await es.search(
                index=secrets.ACTIVE_DATA_INDEX,
                body=query,
            )
            return out['aggregations']['date']['value']

    @staticmethod
    async def calc_revision_coverage(changeset):
        '''
        Calculate total coverage in percent for a changeset
        Directly done through an aggregation on ES
        '''
        query = ActiveDataCoverage.base_query([
            {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
        ])
        query.update({
            # no search results please
            'size': 0,

            'aggs': {
                'percentage': {
                    'avg': {
                        'field': ActiveDataCoverage.FIELD_TOTAL_PERCENT,
                    },
                },
            },
        })
        async with ActiveDataClient() as es:
            out = await es.search(
                index=secrets.ACTIVE_DATA_INDEX,
                body=query,
            )
            return out['aggregations']['percentage']['value']

    @staticmethod
    @alru_cache(maxsize=2048)
    async def get_coverage(changeset):
        '''
        Get total coverage stat for a changeset
        '''

        # Get date of this changeset
        max_date = await ActiveDataCoverage.get_revision_date(changeset)

        # Get previous changeset
        revisions = await ActiveDataCoverage.available_revisions(nb=1, max_date=max_date)
        assert revisions[0]['key'] != changeset, \
            'Should not be the same changeset'

        # Get percentage for current
        current = await ActiveDataCoverage.calc_revision_coverage(changeset)

        # Get percentage for previous
        previous = await ActiveDataCoverage.calc_revision_coverage(revisions[0]['key'])

        return {
            'cur': current,
            'prev': previous,
        }

    @staticmethod
    async def get_file_coverage(changeset, filename):

        # Look for matching file+changeset in queried data
        # This will give us lists of covered lines per test
        nb, tests = await ActiveDataCoverage().list_tests(changeset, filename)
        if not tests:
            return

        # Count all the lines covered per some tests
        lines_covered = itertools.chain(*[
            test['_source']['source']['file']['covered']['~n~']
            for test in tests
        ])

        return dict(collections.Counter(lines_covered))

    @staticmethod
    async def get_latest_build():
        '''
        Gives current and previous revisions as Mercurial SHA1 hashes
        '''
        revisions = await ActiveDataCoverage.available_revisions(nb=2)
        return revisions[0]['key'], revisions[-1]['key']

    @staticmethod
    async def get_push(changeset, repository='mozilla-central'):
        '''
        Load push data for a given changeset on a repository
        '''
        query = {
            '_source': ['push'],
            'query': {
                'bool': {
                    'must': [
                        {'match': {'changeset.id': changeset}},
                        {'match': {'branch.name': repository}},
                    ]
                }
            }
        }
        async with ActiveDataClient() as es:
            out = await es.search(
                index='repo',
                body=query,
            )
            assert out['hits']['total'] == 1, \
                'Push search failed'
            return out['hits']['hits'][0]['_source']['push']
