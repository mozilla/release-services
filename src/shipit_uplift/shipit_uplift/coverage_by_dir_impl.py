# -*- coding: utf-8 -*-
from enum import Enum
import fnmatch
import re
from concurrent.futures import ThreadPoolExecutor
import requests


class CoverageService(Enum):
    COVERALLS = 1
    CODECOV = 2


COVERAGE_SERVICE = CoverageService.CODECOV


def get_mercurial_commit(github_commit):
    url = 'https://api.pub.build.mozilla.org/mapper/gecko-dev/rev/git/%s'
    r = requests.get(url % github_commit)

    return r.text.split(' ')[1]


def load_changesets(rev1, rev2):
    bug_pattern = re.compile('[\t ]*[Bb][Uu][Gg][\t ]*([0-9]+)')

    r = requests.get('https://hg.mozilla.org/mozilla-central/json-pushes?full&fromchange=' + rev1 + '&tochange=' + rev2)

    if r.status_code != requests.codes.ok:
        raise Exception('Error while loading changeset: %s' % r.text)

    pushes = r.json()

    changesets = []

    for pushid, info in pushes.items():
        for changeset in info['changesets']:
            bug_id_match = re.search(bug_pattern, changeset['desc'])
            if not bug_id_match:
                continue

            bug_id = int(bug_id_match.group(1))

            changesets.append((bug_id, changeset['files']))

    return changesets


def get_related_bugs(changesets, directory):
    return list(set([bug for bug, paths in changesets if any(fnmatch.fnmatch(path, directory + '/*') for path in paths)]))


def get_coverage_builds():
    if COVERAGE_SERVICE == CoverageService.COVERALLS:
        r = requests.get('https://coveralls.io/github/marco-c/gecko-dev.json?page=1')
        builds = r.json()['builds']

        latest_commit = builds[0]['commit_sha']
        previous_commit = builds[1]['commit_sha']
    elif COVERAGE_SERVICE == CoverageService.CODECOV:
        r = requests.get('https://codecov.io/api/gh/marco-c/gecko-dev')
        commit = r.json()['commit']

        latest_commit = commit['commitid']
        previous_commit = commit['parent']

    return (latest_commit, previous_commit)


def get_coverage(commit_sha, prev_commit_sha, directory):
    if COVERAGE_SERVICE == CoverageService.COVERALLS:
        r = requests.get('https://coveralls.io/builds/' + commit_sha + '.json?paths=' + directory + '/*')

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()
        files_num = result['selected_source_files_count']
        cur = result['paths_covered_percent']
        prev = result['paths_previous_covered_percent']
    elif COVERAGE_SERVICE == CoverageService.CODECOV:
        r = requests.get('https://codecov.io/api/gh/marco-c/gecko-dev/tree/' + commit_sha + '/' + directory)

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()
        files_num = result['commit']['folder_totals']['files']
        cur = result['commit']['folder_totals']['coverage']

        r = requests.get('https://codecov.io/api/gh/marco-c/gecko-dev/tree/' + prev_commit_sha + '/' + directory)

        if r.status_code != requests.codes.ok:
            raise Exception('Error while loading coverage data.')

        result = r.json()

        prev = result['commit']['folder_totals']['coverage']

    return {
      'files_num': files_num,
      'cur': cur,
      'prev': prev,
    }


def get_directories(directory=''):
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-file/tip/' + directory)
    return [d['abspath'].lstrip('/') for d in r.json()['directories']]


def generate(path):
    latest_commit, previous_commit = get_coverage_builds()

    latest_mercurial_commit = get_mercurial_commit(latest_commit)
    previous_mercurial_commit = get_mercurial_commit(previous_commit)

    changesets = load_changesets(previous_mercurial_commit, latest_mercurial_commit)

    directories = get_directories(path)

    data = dict()
    all_bugs = set()

    def data_for_directory(directory):
        d = get_coverage(latest_commit, previous_commit, directory)

        if d['files_num'] == 0:
            return

        data[directory] = {}
        data[directory]['cur'] = float(d['cur']) if d['cur'] is not None else None
        data[directory]['prev'] = float(d['prev']) if d['prev'] is not None else None

        # Add bugs with structure for libmozdata updates
        directory_bugs = get_related_bugs(changesets, directory)
        all_bugs.update(directory_bugs)
        data[directory]['bugs'] = [
            {
                'id': bug,
                'summary': None,
            }
            for bug in directory_bugs
        ]

    with ThreadPoolExecutor() as executor:
        for directory in directories:
            executor.submit(data_for_directory, directory)

    r = requests.get('https://bugzilla.mozilla.org/rest/bug', params={
      'include_fields': ['id', 'summary'],
      'id': ','.join([str(b) for b in sorted(all_bugs)])
    })

    for found_bug in r.json()['bugs']:
        for directory in data.values():
            for bug in directory['bugs']:
                if bug['id'] == found_bug['id']:
                    bug['summary'] = found_bug['summary']

    return data
