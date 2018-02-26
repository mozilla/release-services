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
    r = requests.get('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s' % mercurial_commit)
    return r.text.split(' ')[0]


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

    @staticmethod
    @abstractmethod
    def get_directory_coverage(changeset, prev_changeset, directory):
        pass


class CoverallsCoverage(Coverage):
    URL = 'https://coveralls.io'

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_coverage(changeset):
        r = requests.get(CoverallsCoverage.URL + '/builds/%s.json' % get_github_commit(changeset))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['covered_percent'],
          'prev': result['covered_percent'] + result['coverage_change'],
        }

    @staticmethod
    def get_file_coverage(changeset, filename):
        r = requests.get(CoverallsCoverage.URL + '/builds/%s/source.json' % get_github_commit(changeset), params={
            'filename': filename,
        })

        if r.status_code != requests.codes.ok:
            return None

        return r.json()

    @staticmethod
    def get_latest_build():
        r = requests.get(CoverallsCoverage.URL + '/github/marco-c/gecko-dev.json?page=1')
        builds = r.json()['builds']

        return builds[0]['commit_sha'], builds[1]['commit_sha']

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_directory_coverage(changeset, prev_changeset, directory):
        r = requests.get(CoverallsCoverage.URL + '/builds/' + get_github_commit(changeset) + '.json?paths=' + directory + '/*')

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        result = r.json()

        return {
          'files_num': result['selected_source_files_count'],
          'cur': result['paths_covered_percent'],
          'prev': result['paths_previous_covered_percent'],
        }


class CodecovCoverage(Coverage):
    @staticmethod
    def _get(url=''):
        return requests.get('https://codecov.io/api/gh/marco-c/gecko-dev%s?access_token=%s' % (url, secrets.CODECOV_ACCESS_TOKEN))

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_coverage(changeset):
        r = CodecovCoverage._get('/commit/%s' % get_github_commit(changeset))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['commit']['totals']['c'],
          'prev': result['commit']['parent_totals']['c'] if result['commit']['parent_totals'] else '?',
        }

    @staticmethod
    def get_file_coverage(changeset, filename):
        r = CodecovCoverage._get('/src/%s/%s' % (get_github_commit(changeset), filename))

        try:
            data = r.json()
        except Exception as e:
            raise CoverageException('Can\'t parse codecov.io report for %s@%s (response: %s)' % (filename, changeset, r.text))

        if r.status_code != requests.codes.ok:
            if data['error']['reason'] == 'File not found in report':
                return None

            raise CoverageException('Can\'t load codecov.io report for %s@%s (response: %s)' % (filename, changeset, r.text))

        return dict([(int(l), v) for l, v in data['commit']['report']['files'][filename]['l'].items()])

    @staticmethod
    def get_latest_build():
        r = CodecovCoverage._get()
        commit = r.json()['commit']

        return commit['commitid'], commit['parent']

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_directory_coverage(changeset, prev_changeset, directory):
        r = CodecovCoverage._get('/tree/%s/%s' % (get_github_commit(changeset), directory))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        cur_result = r.json()

        r = CodecovCoverage._get('/tree/%s/%s' % (get_github_commit(prev_changeset), directory))

        if r.status_code != requests.codes.ok:
            raise CoverageException('Error while loading coverage data.')

        prev_result = r.json()

        return {
          'files_num': cur_result['commit']['folder_totals']['files'],
          'cur': cur_result['commit']['folder_totals']['coverage'],
          'prev': prev_result['commit']['folder_totals']['coverage'],
        }


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

    @staticmethod
    @lru_cache(maxsize=2048)
    def get_directory_coverage(changeset, prev_changeset, directory):
        assert False, 'Not implemented'


coverage_service = CodecovCoverage()


# Push ID to build changeset
MAX_PUSHES = 2048
push_to_changeset_cache = LRUCache(maxsize=MAX_PUSHES)
# Changeset to changeset data (files and push ID)
MAX_CHANGESETS = 2048
changeset_cache = LRUCache(maxsize=MAX_CHANGESETS)


def get_pushes(push_id):
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=%s&endID=%s' % (push_id - 1, push_id + 7))
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
    if changeset not in changeset_cache:
        r = requests.get('https://hg.mozilla.org/mozilla-central/json-rev/%s' % changeset)
        rev = r.json()
        push_id = int(rev['pushid'])

        get_pushes(push_id)

    return changeset_cache[changeset]


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
