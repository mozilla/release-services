# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import aiohttp
from async_lru import alru_cache

from cli_common import log
from codecoverage_backend.services import secrets
from codecoverage_backend.services.base import Coverage
from codecoverage_backend.services.base import CoverageException
from codecoverage_backend.services.base import get_github_commit
from codecoverage_backend.services.base import get_mercurial_commit

logger = log.get_logger(__name__)


class CodecovCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return aiohttp.request('GET', f'https://codecov.io/api/gh/{secrets.CODECOV_REPO}{url}?access_token={secrets.CODECOV_ACCESS_TOKEN}')

    @staticmethod
    @alru_cache(maxsize=2048)
    async def get_coverage(changeset):
        async with CodecovCoverage._get(f'/commit/{await get_github_commit(changeset)}') as r:
            if r.status != 200:
                raise CoverageException('Error while loading coverage data.')

            result = await r.json()

        if result['commit']['state'] == 'error':
            logger.warn(f'{changeset} is in an errored state.')
            raise CoverageException(f'{changeset} is in an errored state.')

        return {
          'cur': result['commit']['totals']['c'],
          'prev': result['commit']['parent_totals']['c'] if result['commit']['parent_totals'] else '?',
        }

    @staticmethod
    async def get_file_coverage(changeset, filename):
        async with CodecovCoverage._get(f'/src/{await get_github_commit(changeset)}/{filename}') as r:
            try:
                data = await r.json()
            except Exception as e:
                logger.exception(e)
                raise CoverageException(f'Can\'t parse codecov.io report for {filename}@{changeset} (response: {r.text})')

            if r.status != 200:
                if data['error']['reason'] == 'File not found in report':
                    return None

                raise CoverageException(f'Can\'t load codecov.io report for {filename}@{changeset} (response: {r.text})')

        if data['commit']['state'] == 'error':
            logger.warn(f'{changeset} is in an errored state.')
            raise CoverageException(f'{changeset} is in an errored state.')

        return dict([(int(l), v) for l, v in data['commit']['report']['files'][filename]['l'].items()])

    @staticmethod
    async def get_latest_build():
        async with CodecovCoverage._get() as r:
            commit = (await r.json())['commit']

        return await get_mercurial_commit(commit['commitid']), await get_mercurial_commit(commit['parent'])
