# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from abc import ABC
from abc import abstractmethod

import aiohttp
from async_lru import alru_cache


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


class CoverageException(Exception):
    pass


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
