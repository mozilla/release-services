# -*- coding: utf-8 -*-
import gzip
import requests

from cli_common.log import get_logger

from shipit_code_coverage import utils


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


def coveralls_wait(job_url):
    def check_coveralls_job():
        r = requests.get(job_url)
        return True if r.json()['covered_percent'] else False

    return utils.wait_until(check_coveralls_job, 60) is not None


def codecov(data, commit_sha, token, flags=None):
    logger.info('Upload report to Codecov')

    params = {
        'commit': commit_sha,
        'token': token,
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
