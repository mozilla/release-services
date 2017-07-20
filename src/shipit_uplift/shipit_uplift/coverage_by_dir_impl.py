# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import fnmatch
import re
import requests

from shipit_uplift.coverage import coverage_service


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


def get_directories(directory=''):
    r = requests.get('https://hg.mozilla.org/mozilla-central/json-file/tip/' + directory)
    return [d['abspath'].lstrip('/') for d in r.json()['directories']]


def generate(path):
    latest_commit, previous_commit = coverage_service.get_latest_build()

    latest_mercurial_commit = get_mercurial_commit(latest_commit)
    previous_mercurial_commit = get_mercurial_commit(previous_commit)

    changesets = load_changesets(previous_mercurial_commit, latest_mercurial_commit)

    directories = get_directories(path)

    data = dict()
    all_bugs = set()

    def data_for_directory(directory):
        d = coverage_service.get_directory_coverage(latest_mercurial_commit, previous_mercurial_commit, directory)

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

    for directory in directories:
        # Ignore hidden directories, as they don't contain any code.
        if directory.startswith('.'):
            continue

        data_for_directory(directory)

    r = requests.get('https://bugzilla.mozilla.org/rest/bug', params={
      'include_fields': ['id', 'summary'],
      'id': ','.join([str(b) for b in sorted(all_bugs)])
    })

    response = r.json()
    found_bugs = response['bugs'] if 'bugs' in response else []

    for found_bug in found_bugs:
        for directory in data.values():
            for bug in directory['bugs']:
                if bug['id'] == found_bug['id']:
                    bug['summary'] = found_bug['summary']

    return data
