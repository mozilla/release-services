# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import aiohttp
from cachetools import LRUCache

from cli_common import log
from codecoverage_backend.services import coverage_service
from codecoverage_backend.services.base import CoverageException

logger = log.get_logger(__name__)


# Push ID to build changeset
MAX_PUSHES = 2048
push_to_changeset_cache = LRUCache(maxsize=MAX_PUSHES)
# Changeset to changeset data (files and push ID)
MAX_CHANGESETS = 2048
changeset_cache = LRUCache(maxsize=MAX_CHANGESETS)


async def get_pushes(push_id):
    async with aiohttp.request('GET', f'https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID={push_id - 1}&endID={push_id + 7}') as r:  # noqa
        data = await r.json()

    for pushid, pushdata in data['pushes'].items():
        pushid = int(pushid)

        push_to_changeset_cache[pushid] = pushdata['changesets'][-1]['node']

        for changeset in pushdata['changesets']:
            is_merge = any(text in changeset['desc'] for text in ['r=merge', 'a=merge'])

            if not is_merge:
                changeset_cache[changeset['node'][:12]] = {
                  'files': changeset['files'],
                  'push': pushid,
                }
            else:
                changeset_cache[changeset['node'][:12]] = {
                  'merge': True,
                  'push': pushid,
                }


async def get_pushes_changesets(push_id, push_id_end):
    if push_id not in push_to_changeset_cache:
        await get_pushes(push_id)

    for i in range(push_id, push_id_end):
        if i not in push_to_changeset_cache:
            continue

        yield push_to_changeset_cache[i]


async def get_changeset_data(changeset):
    if changeset[:12] not in changeset_cache:
        async with aiohttp.request('GET', f'https://hg.mozilla.org/mozilla-central/json-rev/{changeset}') as r:
            rev = await r.json()

        push_id = int(rev['pushid'])

        await get_pushes(push_id)

    return changeset_cache[changeset[:12]]


async def get_coverage_build(changeset):
    '''
    This function returns the first successful coverage build after a given
    changeset.
    '''

    changeset_data = await get_changeset_data(changeset)
    push_id = changeset_data['push']

    # Find the first coverage build after the changeset.
    async for build_changeset in get_pushes_changesets(push_id, push_id + 8):
        try:
            overall = await coverage_service.get_coverage(build_changeset)
            return (changeset_data, build_changeset, overall)
        except CoverageException:
            pass

    assert False, 'Couldn\'t find a build after the changeset'


async def get_latest_build_info():
    latest_rev, previous_rev = await coverage_service.get_latest_build()
    latest_pushid = (await get_changeset_data(latest_rev))['push']
    return {
      'latest_pushid': latest_pushid,
      'latest_rev': latest_rev,
      'previous_rev': previous_rev,
    }


COVERAGE_EXTENSIONS = [
    # C
    'c', 'h',
    # C++
    'cpp', 'cc', 'cxx', 'hh', 'hpp', 'hxx',
    # JavaScript
    'js', 'jsm', 'xul', 'xml', 'html', 'xhtml',
]


def coverage_supported(path):
    return any([path.endswith('.' + ext) for ext in COVERAGE_EXTENSIONS])
