# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from abc import ABC, abstractmethod
import json
import requests

from backend_common.cache import cache


@cache.memoize()
def get_github_commit(mercurial_commit):
    r = requests.get('https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/hg/%s' % mercurial_commit)
    return r.text.split(' ')[0]


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
    @cache.memoize()
    def get_coverage(changeset):
        r = requests.get(CoverallsCoverage.URL + '/builds/%s.json' % get_github_commit(changeset))

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['covered_percent'],
          'prev': result['covered_percent'] + result['coverage_change'],
        }

    @staticmethod
    @cache.memoize()
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
    @cache.memoize()
    def get_directory_coverage(changeset, prev_changeset, directory):
        r = requests.get(CoverallsCoverage.URL + '/builds/' + get_github_commit(changeset) + '.json?paths=' + directory + '/*')

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()

        return {
          'files_num': result['selected_source_files_count'],
          'cur': result['paths_covered_percent'],
          'prev': result['paths_previous_covered_percent'],
        }


class CodecovCoverage(Coverage):
    URL = 'https://codecov.io/api/gh/marco-c/gecko-dev'

    @staticmethod
    @cache.memoize()
    def get_coverage(changeset):
        r = requests.get(CodecovCoverage.URL + '/commit/%s' % get_github_commit(changeset))

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()

        return {
          'cur': result['commit']['totals']['c'],
          'prev': result['commit']['parent_totals']['c'],
        }

    @staticmethod
    @cache.memoize()
    def get_file_coverage(changeset, filename):
        r = requests.get(CodecovCoverage.URL + '/src/%s/%s' % (get_github_commit(changeset), filename))

        data = r.json()

        if r.status_code != requests.codes.ok:
            if data['error']['reason'] == 'File not found in report':
                return None

            raise Exception('Can\'t load codecov.io report')

        return dict([(int(l), v) for l, v in data['commit']['report']['files'][filename]['l'].items()])

    @staticmethod
    def get_latest_build():
        r = requests.get(CodecovCoverage.URL)
        commit = r.json()['commit']

        return commit['commitid'], commit['parent']

    @staticmethod
    @cache.memoize()
    def get_directory_coverage(changeset, prev_changeset, directory):
        r = requests.get(CodecovCoverage.URL + '/tree/' + get_github_commit(changeset) + '/' + directory)

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        cur_result = r.json()

        r = requests.get(CodecovCoverage.URL + '/tree/' + get_github_commit(prev_changeset) + '/' + directory)

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        prev_result = r.json()

        return {
          'files_num': cur_result['commit']['folder_totals']['files'],
          'cur': cur_result['commit']['folder_totals']['coverage'],
          'prev': prev_result['commit']['folder_totals']['coverage'],
        }


class ActiveDataCoverage(Coverage):
    URL = 'https://activedata.allizom.org/query'

    @staticmethod
    def get_coverage(changeset):
        assert False, 'Not implemented'

    @staticmethod
    @cache.memoize()
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
    def get_directory_coverage(changeset, prev_changeset, directory):
        assert False, 'Not implemented'


coverage_service = CodecovCoverage()


def get_coverage_builds(changeset, before=True, after=True):
    '''
    This function returns the last successful build before a given
    changeset and the first successful coverage build after the same
    changeset.
    '''
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-rev/%s' % changeset)
    push_id = int(r.json()['pushid'])

    # In a span of 15 pushes, we hope we will find successful coverage builds.
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-pushes?tipsonly=1&startID=%s&endID=%s' % (push_id - 8, push_id + 7))
    data = r.json()

    before_changeset = None
    before_changeset_overall = None
    after_changeset = None
    after_changeset_overall = None

    pushes = data.items()
    pushes_before = [(pushid, pushdata['changesets'][0]) for pushid, pushdata in pushes if int(pushid) < push_id]
    pushes_after = [(pushid, pushdata['changesets'][0]) for pushid, pushdata in pushes if int(pushid) >= push_id]

    if before:
        # Find the last coverage build before the changeset.
        for pushid, changeset in sorted(pushes_before, reverse=True):
            try:
                before_changeset_overall = coverage_service.get_coverage(changeset)
                before_changeset = changeset
                break
            except:
                pass

        assert before_changeset is not None, 'Couldn\'t find a build before the changeset'

    if after:
        # Find the first coverage build after the changeset.
        for pushid, changeset in sorted(pushes_after):
            try:
                after_changeset_overall = coverage_service.get_coverage(changeset)
                after_changeset = changeset
                break
            except:
                pass

        assert after_changeset is not None, 'Couldn\'t find a build after the changeset'

    return (before_changeset, before_changeset_overall, after_changeset, after_changeset_overall)
