# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from abc import ABC, abstractmethod
import json
from functools import lru_cache
from cachetools import LRUCache
import requests

from shipit_uplift import secrets


@lru_cache(maxsize=2048)
def get_github_commit(mercurial_commit):
    r = requests.get('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/{}'.format(mercurial_commit))
    return r.text.split(' ')[0]


@lru_cache(maxsize=2048)
def get_mercurial_commit(github_commit):
    r = requests.get('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/{}'.format(github_commit))
    return r.text.split(' ')[1]


class CoverageException(Exception):
    pass


class Coverage(ABC):
    @staticmethod
    @abstractmethod
    def get_coverage(changeset):
        pass

    @staticmethod
    @abstractmethod
    def get_file_coverage(changeset, filename):
        pass

    @staticmethod
    @abstractmethod
    def get_latest_build():
        pass


class CoverallsCoverage(Coverage):
    URL = 'https://coveralls.io'

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_coverage(changeset):
        r = requests.get(CoverallsCoverage.URL + '/builds/{}.json'.format(get_github_commit(changeset)))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['covered_percent'],
          'prev': result['covered_percent'] + result['coverage_change'],
        }

    @staticmethod
    def get_file_coverage(changeset, filename):
        r = requests.get(CoverallsCoverage.URL + '/builds/{}/source.json'.format(get_github_commit(changeset)), params={
            'filename': filename,
        })

        if r.status_code != requests.codes.ok:
            return None

        return r.json()

    @staticmethod
    def get_latest_build():
        r = requests.get(CoverallsCoverage.URL + '/github/marco-c/gecko-dev.json?page=1')
        builds = r.json()['builds']

        return get_mercurial_commit(builds[0]['commit_sha']), get_mercurial_commit(builds[1]['commit_sha'])


class CodecovCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return requests.get('https://codecov.io/api/gh/marco-c/gecko-dev{}?access_token={}'.format(url, secrets.CODECOV_ACCESS_TOKEN))

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_coverage(changeset):
        r = CodecovCoverage._get('/commit/{}'.format(get_github_commit(changeset)))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['commit']['totals']['c'],
          'prev': result['commit']['parent_totals']['c'] if result['commit']['parent_totals'] else '?',
        }

    @staticmethod
    def get_file_coverage(changeset, filename):
        r = CodecovCoverage._get('/src/{}/{}'.format(get_github_commit(changeset), filename))

        try:
            data = r.json()
        except Exception as e:
            raise CoverageException('Can\'t parse codecov.io report for {}@{} (response: {})'.format(filename, changeset, r.text))

        if r.status_code != requests.codes.ok:
            if data['error']['reason'] == 'File not found in report':
                return None

            raise CoverageException('Can\'t load codecov.io report for {}@{} (response: {})'.format(filename, changeset, r.text))

        return dict([(int(l), v) for l, v in data['commit']['report']['files'][filename]['l'].items()])

    @staticmethod
    def get_latest_build():
        r = CodecovCoverage._get()
        commit = r.json()['commit']

        return get_mercurial_commit(commit['commitid']), get_mercurial_commit(commit['parent'])


class ActiveDataCoverage(Coverage):
    URL = 'https://activedata.allizom.org/query'

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_coverage(changeset):
        assert False, 'Not implemented'

    @staticmethod
    def get_file_coverage(changeset, filename):
        r = requests.post(ActiveDataCoverage.URL, data=json.dumps({
            'from': 'coverage-summary',
            'where': {
                'and': [
                    {
                        'eq': {
                            'source.file.name': filename,
                        },
                    },
                    {
                        'eq': {
                            'repo.changeset.id12': changeset[:12],
                        },
                    },
                ],
            },
        }))

        f = r.json()['source']['file']
        uncovered = f['uncovered']
        covered = [e['line'] for e in f['covered']]

        all_data = [0] * max(uncovered, covered)
        for c in covered:
            all_data[c] = 1

        return all_data

    @staticmethod
    def get_latest_build():
        assert False, 'Not implemented'


coverage_service = CodecovCoverage()


# Push ID to build changeset
MAX_PUSHES = 2048
push_to_changeset_cache = LRUCache(maxsize=MAX_PUSHES)
# Changeset to changeset data (files and push ID)
MAX_CHANGESETS = 2048
changeset_cache = LRUCache(maxsize=MAX_CHANGESETS)


def get_pushes(push_id):
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID={}&endID={}'.format(push_id - 1, push_id + 7))
    data = r.json()

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


def get_pushes_changesets(push_id, push_id_end):
    if push_id not in push_to_changeset_cache:
        get_pushes(push_id)

    for i in range(push_id, push_id_end):
        if i not in push_to_changeset_cache:
            continue

        yield push_to_changeset_cache[i]


def get_changeset_data(changeset):
    if changeset[:12] not in changeset_cache:
        r = requests.get('https://hg.mozilla.org/mozilla-central/json-rev/{}'.format(changeset))
        rev = r.json()
        push_id = int(rev['pushid'])

        get_pushes(push_id)

    return changeset_cache[changeset[:12]]


def get_coverage_build(changeset):
    '''
    This function returns the first successful coverage build after a given
    changeset.
    '''
    changeset_data = get_changeset_data(changeset)
    push_id = changeset_data['push']

    # Find the first coverage build after the changeset.
    for build_changeset in get_pushes_changesets(push_id, push_id + 8):
        try:
            overall = coverage_service.get_coverage(build_changeset)
            return (changeset_data, build_changeset, overall)
        except CoverageException:
            pass

    assert False, 'Couldn\'t find a build after the changeset'


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
