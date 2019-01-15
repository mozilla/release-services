# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import aiohttp
from async_lru import alru_cache

from codecoverage_backend.services import secrets
from codecoverage_backend.services.base import Coverage
from codecoverage_backend.services.base import CoverageException
from codecoverage_backend.services.base import get_github_commit
from codecoverage_backend.services.base import get_mercurial_commit


class CoverallsCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return aiohttp.request('GET', f'https://coveralls.io{url}')

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
        async with CoverallsCoverage._get(
                '/builds/{}/source.json?filename={}'.format(await get_github_commit(changeset), filename)) as r:
            if r.status != 200:
                return None

            return await r.json()

    @staticmethod
    async def get_latest_build():
        async with CoverallsCoverage._get(f'/github/{secrets.CODECOV_REPO}.json?page=1') as r:
            builds = (await r.json())['builds']

        return await get_mercurial_commit(builds[0]['commit_sha']), await get_mercurial_commit(builds[1]['commit_sha'])
