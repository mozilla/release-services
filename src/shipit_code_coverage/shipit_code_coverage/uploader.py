# -*- coding: utf-8 -*-
import gzip

import requests

from cli_common import utils
from cli_common.log import get_logger
from shipit_code_coverage.secrets import secrets

logger = get_logger(__name__)


def coveralls(data):
    logger.info('Upload report to Coveralls')

    r = requests.post('https://coveralls.io/api/v1/jobs', files={
        'json_file': ('json_file', gzip.compress(data), 'gzip/json')
    })

    try:
        result = r.json()
        logger.info('Uploaded report to Coveralls', report=r.text)
    except ValueError:
        raise Exception('Failure to submit data. Response [%s]: %s' % (r.status_code, r.text))

    return result['url'] + '.json'


def codecov(data, commit_sha, flags=None):
    logger.info('Upload report to Codecov')

    params = {
        'commit': commit_sha,
        'token': secrets[secrets.CODECOV_TOKEN],
        'service': 'custom',
    }

    if flags is not None:
        params['flags'] = ','.join(flags)

    r = requests.post('https://codecov.io/upload/v4', params=params, headers={
        'Accept': 'text/plain',
    })

    if r.status_code != requests.codes.ok:
        raise Exception('Failure to submit data. Response [%s]: %s' % (r.status_code, r.text))

    lines = r.text.splitlines()

    logger.info('Uploaded report to Codecov', report=lines[0])

    data += b'\n<<<<<< EOF'

    r = requests.put(lines[1], data=data, headers={
        'Content-Type': 'text/plain',
        'x-amz-acl': 'public-read',
        'x-amz-storage-class': 'REDUCED_REDUNDANCY',
    })

    if r.status_code != requests.codes.ok:
        raise Exception('Failure to upload data to S3. Response [%s]: %s' % (r.status_code, r.text))


def get_latest_codecov():
    def get_latest_codecov_int():
        r = requests.get('https://codecov.io/api/gh/{}?access_token={}'.format(secrets[secrets.CODECOV_REPO], secrets[secrets.CODECOV_ACCESS_TOKEN]))
        r.raise_for_status()
        return r.json()['commit']['commitid']

    return utils.retry(get_latest_codecov_int)


def codecov_wait(commit):
    class TotalsNoneError(Exception):
        pass

    def check_codecov_job():
        r = requests.get('https://codecov.io/api/gh/{}/commit/{}?access_token={}'.format(secrets[secrets.CODECOV_REPO], commit, secrets[secrets.CODECOV_ACCESS_TOKEN]))  # noqa
        r.raise_for_status()
        totals = r.json()['commit']['totals']
        if totals is None:
            raise TotalsNoneError()
        return True

    try:
        return utils.retry(check_codecov_job, retries=30)
    except TotalsNoneError:
        return False
