import fnmatch
import json
import os
import re
import requests


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
    r = requests.get('https://coveralls.io/github/marco-c/gecko-dev.json?page=1')
    return r.json()['builds']


def get_coverage(commit_sha, directory):
    r = requests.get('https://coveralls.io/builds/' + commit_sha + '.json?paths=' + directory + '/*')

    if r.status_code != requests.codes.ok:
        raise Exception('Error while loading coverage data.')

    return r.json()


def get_directories(directory, rootDir, curLevel=0):
    if curLevel == MAX_LEVEL or '.hg' in directory:
        return []

    dirs = [os.path.relpath(os.path.join(directory, d), rootDir) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    subdirs = []
    for d in dirs:
        subdirs += get_directories(os.path.join(rootDir, d), rootDir, curLevel + 1)

    return dirs + subdirs


def generate(rootDir):
    builds = get_coverage_builds()

    latest_commit = builds[0]['commit_sha']
    previous_commit = builds[1]['commit_sha']
    latest_mercurial_commit = get_mercurial_commit(latest_commit)
    previous_mercurial_commit = get_mercurial_commit(previous_commit)

    changesets = load_changesets(previous_mercurial_commit, latest_mercurial_commit)

    directories = get_directories(rootDir, rootDir)

    data = dict()

    for directory in directories:
        d = get_coverage(latest_commit, directory)

        if d['selected_source_files_count'] == 0:
            continue

        data[directory] = {}
        data[directory]['cur'] = d['paths_covered_percent']
        data[directory]['prev'] = d['paths_previous_covered_percent']
        data[directory]['bugs'] = get_related_bugs(changesets, directory)

    with open('coverage_by_dir.json', 'w') as f:
        json.dump(data, f)
