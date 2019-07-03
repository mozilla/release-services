# -*- coding: utf-8 -*-
import itertools
import os.path

import requests
import structlog
import zstandard as zstd

from code_coverage_bot.secrets import secrets
from code_coverage_bot.utils import retry
from code_coverage_tools.gcp import get_bucket

logger = structlog.get_logger(__name__)
GCP_COVDIR_PATH = '{repository}/{revision}.json.zstd'


def gcp(repository, revision, data):
    '''
    Upload a grcov raw report on Google Cloud Storage
    * Compress with zstandard
    * Upload on bucket using revision in name
    * Trigger ingestion on channel's backend
    '''
    assert isinstance(data, bytes)
    bucket = get_bucket(secrets[secrets.GOOGLE_CLOUD_STORAGE])

    # Compress report
    compressor = zstd.ZstdCompressor()
    archive = compressor.compress(data)

    # Upload archive
    path = GCP_COVDIR_PATH.format(repository=repository, revision=revision)
    blob = bucket.blob(path)
    blob.upload_from_string(archive)

    # Update headers
    blob.content_type = 'application/json'
    blob.content_encoding = 'zstd'
    blob.patch()

    logger.info('Uploaded {} on {}'.format(path, bucket))

    # Trigger ingestion on backend
    retry(lambda: gcp_ingest(repository, revision), retries=5)

    return blob


def gcp_covdir_exists(repository, revision):
    '''
    Check if a covdir report exists on the Google Cloud Storage bucket
    '''
    bucket = get_bucket(secrets[secrets.GOOGLE_CLOUD_STORAGE])
    path = GCP_COVDIR_PATH.format(repository=repository, revision=revision)
    blob = bucket.blob(path)
    return blob.exists()


def gcp_ingest(repository, revision):
    '''
    The GCP report ingestion is triggered remotely on a backend
    by making a simple HTTP request on the /v2/path endpoint
    By specifying the exact new revision processed, the backend
    will download automatically the new report.
    '''
    params = {
        'repository': repository,
        'changeset': revision,
    }
    backend_host = secrets[secrets.BACKEND_HOST]
    resp = requests.get('{}/v2/path'.format(backend_host), params=params)
    resp.raise_for_status()
    logger.info('Ingested report on backend', host=backend_host, repository=repository, revision=revision)
    return resp


def covdir_paths(report):
    '''
    Load a covdir report and recursively list all the paths
    '''
    assert isinstance(report, dict)

    def _extract(obj, base_path=''):
        out = []
        children = obj.get('children', {})
        if children:
            # Recursive on folder files
            out += itertools.chain(*[
                _extract(child, os.path.join(base_path, obj['name']))
                for child in children.values()
            ])

        else:
            # Add full filename
            out.append(os.path.join(base_path, obj['name']))

        return out

    return _extract(report)
