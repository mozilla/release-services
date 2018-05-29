# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import itertools

from async_lru import alru_cache
from elasticsearch_async import AsyncElasticsearch
from esFrontLine.client.async import AsyncHawkConnection

from cli_common import log
from shipit_code_coverage_backend import secrets
from shipit_code_coverage_backend.coverage import Coverage

logger = log.get_logger(__name__)


class ActiveDataClient():
    '''
    Active data async client, through Elastic Search
    '''
    def __init__(self):
        self.client = AsyncElasticsearch(
            hosts=[secrets.ESFRONTLINE['url']],
            connection_class=AsyncHawkConnection,
            hawk_credentials=secrets.ESFRONTLINE['user'],
        )

    async def __aenter__(self):
        # TODO: Should we ping the server here (overkill ?)
        return self.client

    async def __aexit__(self, *args, **kwargs):

        # TODO: Find out why this line fails on
        # RuntimeWarning: coroutine 'ClientSession.close' was never awaited
        # It should remove the warning about unclosed connector
        pass


class ActiveDataCoverage(Coverage):

    FIELD_REPO = 'repo.branch.name.~s~'
    FIELD_FILENAME = 'source.file.name.~s~'
    FIELD_CHANGESET = 'repo.changeset.id.~s~'
    FIELD_CHANGESET_DATE = 'repo.changeset.date.~n~'
    FIELD_TOTAL_PERCENT = 'source.file.percentage_covered.~n~'

    @staticmethod
    async def list_tests(changeset, filename):
        '''
        List all the tests available for file in a changeset
        '''
        filters = [
            # Always query on Mozilla Central
            {'term': {ActiveDataCoverage.FIELD_REPO: 'mozilla-central'}},

            # Filter by filename and changeset
            {'term': {ActiveDataCoverage.FIELD_FILENAME: filename}},
            {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
        ]

        # Build full ES query using mandatory filters
        query = {'query': {'bool': {'must':  filters}}}

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
    async def available_revisions(nb=2, max_date=None):
        '''
        Search the N last revisions available in the ES cluster
        '''

        filters = [
            {'term': {ActiveDataCoverage.FIELD_REPO: 'mozilla-central'}}
        ]

        # Limit search to a maximum date
        if max_date:
            filters.append({
                'range': {
                    ActiveDataCoverage.FIELD_CHANGESET_DATE: {
                        'lt': max_date,
                    },
                },
            })

        query = {
            # no search results please
            'size': 0,

            'query': {
                'bool': {
                    'must': filters,
                },
            },
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
        }

        async with ActiveDataClient() as es:
            out = await es.search(
                index=secrets.ACTIVE_DATA_INDEX,
                body=query,
            )
            return out['aggregations']['revisions']['buckets']

    @staticmethod
    async def get_revision_date(changeset):
        '''
        Get the date of a revision
        '''
        query = {
            # no search results please
            'size': 0,

            'query': {
                'bool': {
                    'must': [
                        {'term': {ActiveDataCoverage.FIELD_REPO: 'mozilla-central'}},
                        {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
                    ],
                },
            },
            'aggs': {
                'date': {
                    'avg': {
                        'field': ActiveDataCoverage.FIELD_CHANGESET_DATE,
                    },
                },
            },
        }
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
        query = {
            # no search results please
            'size': 0,

            'query': {
                'bool': {
                    'must': [
                        {'term': {ActiveDataCoverage.FIELD_REPO: 'mozilla-central'}},
                        {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},
                    ],
                },
            },
            'aggs': {
                'percentage': {
                    'avg': {
                        'field': ActiveDataCoverage.FIELD_TOTAL_PERCENT,
                    },
                },
            },
        }
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
