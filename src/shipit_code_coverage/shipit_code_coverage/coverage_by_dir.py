# -*- coding: utf-8 -*-
from enum import Enum
import fnmatch
import json
import os
import re
import requests
from libmozdata.bugzilla import Bugzilla


class CoverageService(Enum):
    COVERALLS = 1
    CODECOV = 2


COVERAGE_SERVICE = CoverageService.CODECOV
MAX_LEVEL = 3


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
        commits = r.json()['commits']

        latest_commit = commits[0]['commitid']
        previous_commit = commits[1]['commitid']

    return (latest_commit, previous_commit)


def get_coverage(commit_sha, directory):
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
        cur = result['commit']['totals']['c']
        prev = result['commit']['parent_totals']['c']

    return {
      'files_num': files_num,
      'cur': cur,
      'prev': prev,
    }


def get_directories(directory, rootDir, curLevel=0):
    if curLevel == MAX_LEVEL or '.hg' in directory:
        return []

    dirs = [os.path.relpath(os.path.join(directory, d), rootDir) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    subdirs = []
    for d in dirs:
        subdirs += get_directories(os.path.join(rootDir, d), rootDir, curLevel + 1)

    return dirs + subdirs


def generate(rootDir):
    latest_commit, previous_commit = get_coverage_builds()

    latest_mercurial_commit = get_mercurial_commit(latest_commit)
    previous_mercurial_commit = get_mercurial_commit(previous_commit)

    changesets = load_changesets(previous_mercurial_commit, latest_mercurial_commit)

    directories = get_directories(rootDir, rootDir)

    data = dict()
    all_bugs = set()

    for directory in directories:
        d = get_coverage(latest_commit, directory)

        if d['files_num'] == 0:
            continue

        data[directory] = {}
        data[directory]['cur'] = d['cur']
        data[directory]['prev'] = d['prev']

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

    def _bughandler(bug, *args, **kwargs):
        for directory in data.values():
            bug_id = bug['id']
            for b in directory['bugs']:
                if b['id'] == bug_id:
                    b.update(bug)

    Bugzilla(
        all_bugs,
        bughandler=_bughandler,
        include_fields=(
            'id',
            'summary',
        )
    ).get_data().wait()

    with open('coverage_by_dir.json', 'w') as f:
        json.dump(data, f)
