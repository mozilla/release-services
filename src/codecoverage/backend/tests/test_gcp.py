# -*- coding: utf-8 -*-
import hashlib
import json
import os
import uuid

import pytest


def test_store_push(mock_cache):
    '''
    Test base method to store a push & changesets on redis
    '''
    assert mock_cache.redis.keys('*') == []
    mock_cache.store_push('myrepo', 1234, ['deadbeef', 'coffee'], 111222333)

    assert mock_cache.redis.keys('*') == [b'changeset:myrepo:deadbeef', b'changeset:myrepo:coffee']
    assert mock_cache.redis.hgetall('changeset:myrepo:deadbeef') == {
        b'push': b'1234',
        b'date': b'111222333',
    }
    assert mock_cache.redis.hgetall('changeset:myrepo:coffee') == {
        b'push': b'1234',
        b'date': b'111222333',
    }


def test_download_report(mock_cache):
    '''
    Test base method to download a report & store it on local FS
    '''
    mock_cache.bucket.add_mock_blob('myrepo/deadbeef123.json.zstd')

    # Does not exist
    assert mock_cache.download_report('myrepo', 'missing') is False

    archive = os.path.join(mock_cache.reports_dir, 'myrepo', 'deadbeef123.json.zstd')
    payload = os.path.join(mock_cache.reports_dir, 'myrepo', 'deadbeef123.json')
    assert not os.path.exists(archive)
    assert not os.path.exists(payload)

    # Valid blob
    assert mock_cache.download_report('myrepo', 'deadbeef123') == payload

    # Only the payload remains after download
    assert not os.path.exists(archive)
    assert os.path.exists(payload)

    assert json.load(open(payload)) == {
        'children': {},
        'coveragePercent': 0.0,
    }


def test_ingestion(mock_cache):
    '''
    Test ingestion of several reports and their retrieval through Redis index
    '''
    # Setup blobs
    mock_cache.bucket.add_mock_blob('myrepo/rev1.json.zstd', coverage=0.1)
    mock_cache.bucket.add_mock_blob('myrepo/rev2.json.zstd', coverage=0.2)
    mock_cache.bucket.add_mock_blob('myrepo/rev10.json.zstd', coverage=1.0)

    # No reports at first
    assert mock_cache.redis.zcard(b'reports:myrepo') == 0
    assert mock_cache.redis.zcard(b'history:myrepo') == 0
    assert mock_cache.list_reports('myrepo') == []

    # Ingest those 3 reports
    mock_cache.ingest_report('myrepo', 1, 'rev1', 1000)
    mock_cache.ingest_report('myrepo', 2, 'rev2', 2000)
    mock_cache.ingest_report('myrepo', 10, 'rev10', 9000)

    # They must be in redis and on the file system
    assert mock_cache.redis.zcard(b'reports:myrepo') == 3
    assert mock_cache.redis.zcard(b'history:myrepo') == 3
    assert os.path.exists(os.path.join(mock_cache.reports_dir, 'myrepo', 'rev1.json'))
    assert os.path.exists(os.path.join(mock_cache.reports_dir, 'myrepo', 'rev2.json'))
    assert os.path.exists(os.path.join(mock_cache.reports_dir, 'myrepo', 'rev10.json'))

    # Reports are exposed, and sorted by push
    assert mock_cache.list_reports('another') == []
    assert mock_cache.list_reports('myrepo') == [
        ('rev10', 10),
        ('rev2', 2),
        ('rev1', 1),
    ]
    assert mock_cache.find_report('myrepo') == ('rev10', 10)
    assert mock_cache.get_history('myrepo', start=200, end=20000) == [
        {'changeset': 'rev10', 'coverage': 1.0, 'date': 9000},
        {'changeset': 'rev2', 'coverage': 0.2, 'date': 2000},
        {'changeset': 'rev1', 'coverage': 0.1, 'date': 1000},
    ]

    # Even if we add a smaller one later on, reports are still sorted
    mock_cache.bucket.add_mock_blob('myrepo/rev5.json.zstd', coverage=0.5)
    mock_cache.ingest_report('myrepo', 5, 'rev5', 5000)
    assert mock_cache.list_reports('myrepo') == [
        ('rev10', 10),
        ('rev5', 5),
        ('rev2', 2),
        ('rev1', 1),
    ]
    assert mock_cache.find_report('myrepo') == ('rev10', 10)
    assert mock_cache.find_report('myrepo', max_push_id=7) == ('rev5', 5)
    assert mock_cache.get_history('myrepo', start=200, end=20000) == [
        {'changeset': 'rev10', 'coverage': 1.0, 'date': 9000},
        {'changeset': 'rev5', 'coverage': 0.5, 'date': 5000},
        {'changeset': 'rev2', 'coverage': 0.2, 'date': 2000},
        {'changeset': 'rev1', 'coverage': 0.1, 'date': 1000},
    ]


def test_ingest_hgmo(mock_cache, mock_hgmo):
    '''
    Test ingestion using a mock HGMO
    '''

    # Add a report on push 995
    rev = hashlib.md5(b'995').hexdigest()
    mock_cache.bucket.add_mock_blob('myrepo/{}.json.zstd'.format(rev), coverage=0.5)

    # Ingest last pushes
    assert mock_cache.list_reports('myrepo') == []
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) == 0
    mock_cache.ingest_pushes('myrepo')
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) > 0
    assert mock_cache.list_reports('myrepo') == [
        (rev, 995)
    ]


def test_closest_report(mock_cache, mock_hgmo):
    '''
    Test algo to find the closest report for any changeset
    '''
    # Build revision for push 992
    revision = '992{}'.format(uuid.uuid4().hex[3:])

    # No data at first
    assert mock_cache.redis.zcard('reports') == 0
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) == 0

    # Try to find a report, but none is available
    with pytest.raises(Exception) as e:
        mock_cache.find_closest_report('myrepo', revision)
    assert str(e.value) == 'No report found'

    # Some pushes were ingested though
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) > 0

    # Add a report on 994, 2 pushes after our revision
    report_rev = hashlib.md5(b'994').hexdigest()
    mock_cache.bucket.add_mock_blob('myrepo/{}.json.zstd'.format(report_rev), coverage=0.5)

    # Now we have a report !
    assert mock_cache.list_reports('myrepo') == []
    assert mock_cache.find_closest_report('myrepo', revision) == (report_rev, 994)
    assert mock_cache.list_reports('myrepo') == [
        (report_rev, 994)
    ]
