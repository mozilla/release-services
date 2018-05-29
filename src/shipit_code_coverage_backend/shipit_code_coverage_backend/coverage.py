# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import itertools
from abc import ABC
from abc import abstractmethod

import aiohttp
from async_lru import alru_cache
from cachetools import LRUCache
from elasticsearch_async import AsyncElasticsearch
from esFrontLine.client.async import AsyncHawkConnection

from cli_common import log
from shipit_code_coverage_backend import secrets

logger = log.get_logger(__name__)


@alru_cache(maxsize=2048)
async def get_github_commit(mercurial_commit):
    async with aiohttp.request('GET', 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/{}'.format(mercurial_commit)) as r:
        text = await r.text()
        return text.split(' ')[0]


@alru_cache(maxsize=2048)
async def get_mercurial_commit(github_commit):
    async with aiohttp.request('GET', 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/{}'.format(github_commit)) as r:
        text = await r.text()
        return text.split(' ')[1]


class CoverageException(Exception):
    pass


class Coverage(ABC):
    @staticmethod
    @abstractmethod
    async def get_coverage(changeset):
        pass

    @staticmethod
    @abstractmethod
    async def get_file_coverage(changeset, filename):
        pass

    @staticmethod
    @abstractmethod
    async def get_latest_build():
        pass


class CoverallsCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return aiohttp.request('GET', 'https://coveralls.io{}'.format(url))

    @staticmethod
    @alru_cache(maxsize=2048)
    async def get_coverage(changeset):
        async with CoverallsCoverage._get('/builds/{}.json'.format(await get_github_commit(changeset))) as r:
            if r.status != 200:
                raise CoverageException('Error while loading coverage data.')

            result = await r.json()

        return {
          'cur': result['covered_percent'],
          'prev': result['covered_percent'] + result['coverage_change'],
        }

    @staticmethod
    async def get_file_coverage(changeset, filename):
        async with CoverallsCoverage._get('/builds/{}/source.json?filename={}'.format(await get_github_commit(changeset), filename)) as r:
            if r.status != 200:
                return None

            return await r.json()

    @staticmethod
    async def get_latest_build():
        async with CoverallsCoverage._get('/github/{}.json?page=1'.format(secrets.CODECOV_REPO)) as r:
            builds = (await r.json())['builds']

        return await get_mercurial_commit(builds[0]['commit_sha']), await get_mercurial_commit(builds[1]['commit_sha'])


class CodecovCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return aiohttp.request('GET', 'https://codecov.io/api/gh/{}{}?access_token={}'.format(secrets.CODECOV_REPO, url, secrets.CODECOV_ACCESS_TOKEN))

    @staticmethod
    @alru_cache(maxsize=2048)
    async def get_coverage(changeset):
        async with CodecovCoverage._get('/commit/{}'.format(await get_github_commit(changeset))) as r:
            if r.status != 200:
                raise CoverageException('Error while loading coverage data.')

            result = await r.json()

        if result['commit']['state'] == 'error':
            logger.warn('{} is in an errored state.'.format(changeset))
            raise CoverageException('{} is in an errored state.'.format(changeset))

        return {
          'cur': result['commit']['totals']['c'],
          'prev': result['commit']['parent_totals']['c'] if result['commit']['parent_totals'] else '?',
        }

    @staticmethod
    async def get_file_coverage(changeset, filename):
        async with CodecovCoverage._get('/src/{}/{}'.format(await get_github_commit(changeset), filename)) as r:
            try:
                data = await r.json()
            except Exception as e:
                raise CoverageException('Can\'t parse codecov.io report for %s@%s (response: %s)' % (filename, changeset, r.text))

            if r.status != 200:
                if data['error']['reason'] == 'File not found in report':
                    return None

                raise CoverageException('Can\'t load codecov.io report for %s@%s (response: %s)' % (filename, changeset, r.text))

        if data['commit']['state'] == 'error':
            logger.warn('{} is in an errored state.'.format(changeset))
            raise CoverageException('{} is in an errored state.'.format(changeset))

        return dict([(int(l), v) for l, v in data['commit']['report']['files'][filename]['l'].items()])

    @staticmethod
    async def get_latest_build():
        async with CodecovCoverage._get() as r:
            commit = (await r.json())['commit']

        return await get_mercurial_commit(commit['commitid']), await get_mercurial_commit(commit['parent'])


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


coverage_service = CodecovCoverage()


# Push ID to build changeset
MAX_PUSHES = 2048
push_to_changeset_cache = LRUCache(maxsize=MAX_PUSHES)
# Changeset to changeset data (files and push ID)
MAX_CHANGESETS = 2048
changeset_cache = LRUCache(maxsize=MAX_CHANGESETS)


async def get_pushes(push_id):
    async with aiohttp.request('GET', 'https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID={}&endID={}'.format(push_id - 1, push_id + 7)) as r:  # noqa
        data = await r.json()

    for pushid, pushdata in data['pushes'].items():
        pushid = int(pushid)

        push_to_changeset_cache[pushid] = pushdata['changesets'][-1]['node']

        for changeset in pushdata['changesets']:
            is_merge = any(text in changeset['desc'] for text in ['r=merge', 'a=merge'])

            if not is_merge:
                changeset_cache[changeset['node'][:12]] = {
                  'files': changeset['files'],
                  'push': pushid,
                }
            else:
                changeset_cache[changeset['node'][:12]] = {
                  'merge': True,
                  'push': pushid,
                }


async def get_pushes_changesets(push_id, push_id_end):
    if push_id not in push_to_changeset_cache:
        await get_pushes(push_id)

    for i in range(push_id, push_id_end):
        if i not in push_to_changeset_cache:
            continue

        yield push_to_changeset_cache[i]


async def get_changeset_data(changeset):
    if changeset[:12] not in changeset_cache:
        async with aiohttp.request('GET', 'https://hg.mozilla.org/mozilla-central/json-rev/{}'.format(changeset)) as r:
            rev = await r.json()

        push_id = int(rev['pushid'])

        await get_pushes(push_id)

    return changeset_cache[changeset[:12]]


async def get_coverage_build(changeset):
    '''
    This function returns the first successful coverage build after a given
    changeset.
    '''
    changeset_data = await get_changeset_data(changeset)
    push_id = changeset_data['push']

    # Find the first coverage build after the changeset.
    async for build_changeset in get_pushes_changesets(push_id, push_id + 8):
        try:
            overall = await coverage_service.get_coverage(build_changeset)
            return (changeset_data, build_changeset, overall)
        except CoverageException:
            pass

    assert False, 'Couldn\'t find a build after the changeset'


async def get_latest_build_info():
    latest_rev, previous_rev = await coverage_service.get_latest_build()
    latest_pushid = (await get_changeset_data(latest_rev))['push']
    return {
      'latest_pushid': latest_pushid,
      'latest_rev': latest_rev,
      'previous_rev': previous_rev,
    }


COVERAGE_EXTENSIONS = [
    # C
    'c', 'h',
    # C++
    'cpp', 'cc', 'cxx', 'hh', 'hpp', 'hxx',
    # JavaScript
    'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
]


def coverage_supported(path):
    return any([path.endswith('.' + ext) for ext in COVERAGE_EXTENSIONS])
