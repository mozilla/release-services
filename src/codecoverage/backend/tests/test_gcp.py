# -*- coding: utf-8 -*-
import hashlib
import json
import os


def test_store_push(mock_cache):
    '''
    Test base method to store a push & changesets on redis
    '''
    assert mock_cache.redis.keys('*') == []
    mock_cache.store_push('myrepo', 1234, ['deadbeef', 'coffee'])

    assert mock_cache.redis.keys('*') == [b'changeset:myrepo:deadbeef', b'changeset:myrepo:coffee']
    assert mock_cache.redis.hgetall('changeset:myrepo:deadbeef') == {
        b'push': b'1234'
    }
    assert mock_cache.redis.hgetall('changeset:myrepo:coffee') == {
        b'push': b'1234'
    }


def test_download_report(mock_cache):
    '''
    Test base method to download a report & store it on local FS
    '''
    mock_cache.bucket.add_mock_blob('myrepo/deadbeef123.json.zstd', b'["test"]')

    # Does not exist
    assert mock_cache.download_report('myrepo', 'missing') is False

    archive = os.path.join(mock_cache.reports_dir, 'myrepo', 'deadbeef123.json.zstd')
    payload = os.path.join(mock_cache.reports_dir, 'myrepo', 'deadbeef123.json')
    assert not os.path.exists(archive)
    assert not os.path.exists(payload)

    # Valid blob
    assert mock_cache.download_report('myrepo', 'deadbeef123') is True

    # Files are now on FS
    assert os.path.exists(archive)
    assert os.path.exists(payload)

    assert json.load(open(payload)) == ['test']


def test_ingestion(mock_cache):
    '''
    Test ingestion of several reports and their retrieval through Redis index
    '''
    # Setup blobs
    mock_cache.bucket.add_mock_blob('myrepo/rev1.json.zstd', b'["coverage 1"]')
    mock_cache.bucket.add_mock_blob('myrepo/rev2.json.zstd', b'["coverage 2"]')
    mock_cache.bucket.add_mock_blob('myrepo/rev10.json.zstd', b'["coverage 10"]')

    # No reports at first
    assert mock_cache.redis.zcard(b'reports:myrepo') == 0
    assert mock_cache.list_reports('myrepo') == []

    # Ingest those 3 reports
    mock_cache.ingest_report('myrepo', 1, 'rev1')
    mock_cache.ingest_report('myrepo', 2, 'rev2')
    mock_cache.ingest_report('myrepo', 10, 'rev10')

    # They must be in redis and on the file system
    assert mock_cache.redis.zcard(b'reports:myrepo') == 3
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

    # Even if we add a smaller one later on, reports are still sorted
    mock_cache.bucket.add_mock_blob('myrepo/rev5.json.zstd', b'["coverage 5"]')
    mock_cache.ingest_report('myrepo', 5, 'rev5')
    assert mock_cache.list_reports('myrepo') == [
        ('rev10', 10),
        ('rev5', 5),
        ('rev2', 2),
        ('rev1', 1),
    ]
    assert mock_cache.find_report('myrepo') == ('rev10', 10)
    assert mock_cache.find_report('myrepo', max_push_id=7) == ('rev5', 5)


def test_ingest_hgmo(mock_cache, mock_hgmo):
    '''
    Test ingestion using a mock HGMO
    '''

    # Add a report on push 995
    rev = hashlib.md5(b'995').hexdigest()
    mock_cache.bucket.add_mock_blob('myrepo/{}.json.zstd'.format(rev), b'["some coverage"]')

    # Ingest last pushes
    assert mock_cache.redis.zcard('reports') == 0
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) == 0
    mock_cache.ingest_pushes('myrepo')
    assert len(mock_cache.redis.keys('changeset:myrepo:*')) > 0
    assert mock_cache.redis.zcard('reports') == 0
    assert mock_cache.list_reports('myrepo') == [
        (rev, 995)
    ]
