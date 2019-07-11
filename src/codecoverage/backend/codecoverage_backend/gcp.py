# -*- coding: utf-8 -*-
import calendar
import math
import os
import tempfile
from datetime import datetime

import redis
import requests
import structlog
import zstandard as zstd
from dateutil.relativedelta import relativedelta

from code_coverage_tools.gcp import get_bucket
from codecoverage_backend import covdir
from codecoverage_backend import taskcluster

logger = structlog.get_logger(__name__)
__cache = None

KEY_REPORTS = 'reports:{repository}'
KEY_CHANGESET = 'changeset:{repository}:{changeset}'
KEY_HISTORY = 'history:{repository}'
KEY_OVERALL_COVERAGE = 'overall:{repository}:{changeset}'

HGMO_REVISION_URL = 'https://hg.mozilla.org/{repository}/json-rev/{revision}'
HGMO_PUSHES_URL = 'https://hg.mozilla.org/{repository}/json-pushes'

REPOSITORIES = ('mozilla-central', )

MIN_PUSH = 0
MAX_PUSH = math.inf


def load_cache():
    '''
    Manage singleton instance of GCPCache when configuration is available
    '''
    global __cache

    if taskcluster.secrets['GOOGLE_CLOUD_STORAGE'] is None:
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
        self.redis = redis.from_url(taskcluster.secrets['REDIS_URL'])
        assert self.redis.ping(), 'Redis server does not ping back'

        # Open gcp connection to bucket
        assert taskcluster.secrets['GOOGLE_CLOUD_STORAGE'] is not None, \
            'Missing GOOGLE_CLOUD_STORAGE secret'
        self.bucket = get_bucket(taskcluster.secrets['GOOGLE_CLOUD_STORAGE'])

        # Local storage for reports
        self.reports_dir = reports_dir or os.path.join(tempfile.gettempdir(), 'ccov-reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        logger.info('Reports will be stored in {}'.format(self.reports_dir))

        # Load most recent reports in cache
        for repo in REPOSITORIES:
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
                date = push['date']
                self.store_push(repository, push_id, changesets, date)

                reports = [
                    changeset
                    for changeset in changesets
                    if self.ingest_report(repository, push_id, changeset, date)
                ]
                if reports:
                    logger.info('Found reports in that push', push_id=push_id)

            newest = pushes[-1][0]
            params['startID'] = newest
            params['endID'] = newest + chunk_size

    def ingest_report(self, repository, push_id, changeset, date):
        '''
        When a report exist for a changeset, download it and update redis data
        '''
        assert isinstance(push_id, int)
        assert isinstance(date, int)

        # Download the report
        report_path = self.download_report(repository, changeset)
        if not report_path:
            return False

        # Read overall coverage for history
        key = KEY_OVERALL_COVERAGE.format(
            repository=repository,
            changeset=changeset,
        )
        report = covdir.open_report(report_path)
        assert report is not None, 'No report to ingest'
        overall_coverage = covdir.get_overall_coverage(report)
        assert len(overall_coverage) > 0, 'No overall coverage'
        self.redis.hmset(key, overall_coverage)

        # Add the changeset to the sorted sets of known reports
        # The numeric push_id is used as a score to keep the ingested
        # changesets ordered
        self.redis.zadd(KEY_REPORTS.format(repository=repository), {changeset: push_id})

        # Add the changeset to the sorted sets of known reports by date
        self.redis.zadd(KEY_HISTORY.format(repository=repository), {changeset: date})

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
            return json_path

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

        os.unlink(archive_path)
        logger.info('Decompressed report', path=json_path)
        return json_path

    def store_push(self, repository, push_id, changesets, date):
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
            self.redis.hmset(key, {
                'push': push_id,
                'date': date,
            })

        logger.info('Stored new push data', push_id=push_id)

    def find_report(self, repository, push_range=(MAX_PUSH, MIN_PUSH)):
        '''
        Find the first report available before that push
        '''
        results = self.list_reports(
            repository,
            nb=1,
            push_range=push_range,
        )
        if not results:
            raise Exception('No report found')
        return results[0]

    def find_closest_report(self, repository, changeset):
        '''
        Find the closest report from specified changeset:
        1. Lookup the changeset push in cache
        2. Lookup the changeset push in HGMO
        3. Find the first report after that push
        '''

        # Lookup push from cache (fast)
        key = KEY_CHANGESET.format(
            repository=repository,
            changeset=changeset,
        )
        push_id = self.redis.hget(key, 'push')
        if push_id:
            # Redis lib uses bytes for all output
            push_id = int(push_id.decode('utf-8'))
        else:

            # Lookup push from HGMO (slow)
            url = HGMO_REVISION_URL.format(
                repository=repository,
                revision=changeset,
            )
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            assert 'pushid' in data, 'Missing pushid'
            push_id = data['pushid']

            # Ingest pushes as we clearly don't have it in cache
            self.ingest_pushes(repository, min_push_id=push_id-1, nb_pages=1)

        # Load report from that push
        return self.find_report(repository, push_range=(push_id, MAX_PUSH))

    def list_reports(self, repository, nb=5, push_range=(MAX_PUSH, MIN_PUSH)):
        '''
        List the last reports available on the server, ordered by push
        by default from newer to older
        The order is detected from the push range
        '''
        assert isinstance(nb, int)
        assert nb > 0
        assert isinstance(push_range, tuple) and len(push_range) == 2

        # Detect ordering from push range
        start, end = push_range
        op = self.redis.zrangebyscore if start < end else self.redis.zrevrangebyscore

        reports = op(
            KEY_REPORTS.format(repository=repository),
            start, end,
            start=0,
            num=nb,
            withscores=True,
        )

        return [
            (changeset.decode('utf-8'), int(push))
            for changeset, push in reports
        ]

    def get_coverage(self, repository, changeset, path):
        '''
        Load a report and its coverage for a specific path
        and build a serializable representation
        '''
        report_path = os.path.join(self.reports_dir, '{}/{}.json'.format(repository, changeset))

        report = covdir.open_report(report_path)
        if report is None:
            # Try to download the report if it's missing locally
            report_path = self.download_report(repository, changeset)
            assert report_path is not False, \
                'Missing report for {} at {}'.format(repository, changeset)

            report = covdir.open_report(report_path)
            assert report

        out = covdir.get_path_coverage(report, path)
        out['changeset'] = changeset
        return out

    def get_history(self, repository, path='', start=None, end=None):
        '''
        Load the history overall coverage from the redis cache
        Default to date range from now back to a year
        '''
        if end is None:
            end = calendar.timegm(datetime.utcnow().timetuple())
        if start is None:
            start = datetime.fromtimestamp(end) - relativedelta(years=1)
            start = int(datetime.timestamp(start))
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert end > start

        # Load changesets ordered by date, in that range
        history = self.redis.zrevrangebyscore(
            KEY_HISTORY.format(repository=repository),
            end, start,
            withscores=True,
        )

        def _coverage(changeset, date):
            # Load overall coverage for specified path
            changeset = changeset.decode('utf-8')
            key = KEY_OVERALL_COVERAGE.format(
                repository=repository,
                changeset=changeset,
            )
            coverage = self.redis.hget(key, path)
            if coverage is not None:
                coverage = float(coverage)
            return {
                'changeset': changeset,
                'date': int(date),
                'coverage': coverage,
            }

        return [
            _coverage(changeset, date)
            for changeset, date in history
        ]
