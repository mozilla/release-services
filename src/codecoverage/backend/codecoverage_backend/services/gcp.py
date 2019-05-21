# -*- coding: utf-8 -*-
import os
import tempfile

import redis
import requests
import zstandard as zstd

from cli_common import log
from cli_common.gcp import get_bucket
from codecoverage_backend import covdir
from codecoverage_backend import secrets

logger = log.get_logger(__name__)
__cache = None

KEY_REPORTS = 'reports:{repository}'
KEY_CHANGESET = 'changeset:{repository}:{changeset}'

HGMO_REVISION_URL = 'https://hg.mozilla.org/{repository}/json-rev/{revision}'
HGMO_PUSHES_URL = 'https://hg.mozilla.org/{repository}/json-pushes'


def load_cache():
    '''
    Manage singleton instance of GCPCache when configuration is available
    '''
    global __cache

    if secrets.GOOGLE_CLOUD_STORAGE is None:
        return

    if __cache is None:
        __cache = GCPCache()

    return __cache


class GCPCache(object):
    '''
    Cache on Redis GCP results
    '''
    def __init__(self, reports_dir=None):
        # Open redis connection
        self.redis = redis.from_url(secrets.REDIS_URL)
        assert self.redis.ping(), 'Redis server does not ping back'

        # Open gcp connection to bucket
        assert secrets.GOOGLE_CLOUD_STORAGE is not None, \
            'Missing GOOGLE_CLOUD_STORAGE secret'
        self.bucket = get_bucket(secrets.GOOGLE_CLOUD_STORAGE)

        # Local storage for reports
        self.reports_dir = reports_dir or os.path.join(tempfile.gettempdir(), 'ccov-reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        logger.info('Reports will be stored in {}'.format(self.reports_dir))

        # Load most recent reports in cache
        for repo in ('mozilla-central', ):
            for rev, _ in self.list_reports(repo, nb=1):
                self.download_report(repo, rev)

    def ingest_pushes(self, repository, min_push_id=None, nb_pages=3):
        '''
        Ingest HGMO changesets and pushes into our Redis Cache
        The pagination goes from oldest to newest, starting from the optional min_push_id
        '''
        chunk_size = 8
        params = {
            'version': 2,
        }
        if min_push_id is not None:
            assert isinstance(min_push_id, int)
            params['startID'] = min_push_id
            params['endID'] = min_push_id + chunk_size

        for page in range(nb_pages):

            r = requests.get(HGMO_PUSHES_URL.format(repository=repository), params=params)
            data = r.json()

            # Sort pushes to go from oldest to newest
            pushes = sorted([
                (int(push_id), push)
                for push_id, push in data['pushes'].items()
            ], key=lambda p: p[0])
            if not pushes:
                return

            for push_id, push in pushes:

                changesets = push['changesets']
                self.store_push(repository, push_id, changesets)

                reports = [
                    changeset
                    for changeset in changesets
                    if self.ingest_report(repository, push_id, changeset)
                ]
                if reports:
                    logger.info('Found reports in that push', push_id=push_id)

            newest = pushes[-1][0]
            params['startID'] = newest
            params['endID'] = newest + chunk_size

    def ingest_report(self, repository, push_id, changeset):
        '''
        When a report exist for a changeset, download it and update redis data
        '''
        assert isinstance(push_id, int)

        # Download the report
        if not self.download_report(repository, changeset):
            return

        # Add the changeset to the sorted sets of known reports
        # The numeric push_id is used as a score to keep the ingested
        # changesets ordered
        self.redis.zadd(KEY_REPORTS.format(repository=repository), {changeset: push_id})

        logger.info('Ingested report', changeset=changeset)
        return True

    def download_report(self, repository, changeset):
        '''
        Download and extract a json+zstd covdir report
        '''
        # Chek the report is available on remote storage
        path = '{}/{}.json.zstd'.format(repository, changeset)
        blob = self.bucket.blob(path)
        if not blob.exists():
            logger.debug('No report found on GCP', path=path)
            return False

        archive_path = os.path.join(self.reports_dir, blob.name)
        json_path = os.path.join(self.reports_dir, blob.name.rstrip('.zstd'))
        if os.path.exists(json_path):
            logger.info('Report already available', path=json_path)
            return True

        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        blob.download_to_filename(archive_path)
        logger.info('Downloaded report archive', path=archive_path)

        with open(json_path, 'wb') as output:
            with open(archive_path, 'rb') as archive:
                dctx = zstd.ZstdDecompressor()
                reader = dctx.stream_reader(archive)
                while True:
                    chunk = reader.read(16384)
                    if not chunk:
                        break
                    output.write(chunk)

        logger.info('Decompressed report', path=json_path)
        return True

    def store_push(self, repository, push_id, changesets):
        '''
        Store a push on redis cache, with its changesets
        '''
        assert isinstance(push_id, int)
        assert isinstance(changesets, list)

        # Store changesets initial data
        for changeset in changesets:
            key = KEY_CHANGESET.format(
                repository=repository,
                changeset=changeset,
            )
            self.redis.hset(key, 'push', push_id)

        logger.info('Stored new push data', push_id=push_id)

    def find_report(self, repository, min_push_id=None, max_push_id=None):
        '''
        Find the first report available before that push
        '''
        results = self.list_reports(repository, nb=1, min_push_id=min_push_id, max_push_id=max_push_id)
        if not results:
            raise Exception('No report found')
        return results[0]

    def find_closest_report(self, repository, revision):
        '''
        Find the closest report from specified revision:
        1. Lookup the revision push in cache
        2. Lookup the revision push in HGMO
        3. Find the first report after that push
        '''

        # Lookup push from cache (fast)
        key = KEY_CHANGESET.format(
            repository=repository,
            changeset=revision,
        )
        push_id = self.redis.hget(key, 'push')
        if not push_id:

            # Lookup push from HGMO (slow)
            url = HGMO_REVISION_URL.format(
                repository=repository,
                revision=revision,
            )
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            assert 'pushid' in data, 'Missing pushid'
            push_id = data['pushid']

            # Ingest pushes as we clearly don't have it in cache
            self.ingest_pushes(repository, min_push_id=push_id-1, nb_pages=1)

        # Load report from that push
        return self.find_report(repository, min_push_id=push_id)

    def list_reports(self, repository, nb=5, min_push_id=None, max_push_id=None):
        '''
        List the last reports available on the server
        When max_push_id is not set, we use the whole range
        '''
        assert isinstance(nb, int)
        assert nb > 0
        start = max_push_id or '+inf'
        end = min_push_id or '-inf'
        reports = self.redis.zrevrangebyscore(
            KEY_REPORTS.format(repository=repository),
            start, end,
            start=0,
            num=nb,
            withscores=True,
        )

        return [
            (revision.decode('utf-8'), int(push))
            for revision, push in reports
        ]

    def get_coverage(self, repository, changeset, path):
        '''
        Load a report and its coverage for a specific path
        and build a serializable representation
        '''
        report_path = os.path.join(self.reports_dir, '{}/{}.json'.format(repository, changeset))
        assert os.path.exists(report_path), 'Missing report {}'.format(report_path)

        return covdir.get_path_coverage(report_path, path)
