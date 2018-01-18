# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import shutil
import sqlite3
import tarfile
import requests
import whatthepatch
from shipit_uplift.coverage import coverage_supported


def download_mapping():
    try:
        with open('chunk_mapping.etag', 'r') as f:
            etag = f.read()
    except:
        etag = ''

    CHUNK_MAPPING_URL = 'https://raw.githubusercontent.com/marco-c/code-coverage-reports/master/chunk_mapping.tar.xz'

    r = requests.head(CHUNK_MAPPING_URL)
    if r.headers['ETag'] != etag:
        r = requests.get(CHUNK_MAPPING_URL, stream=True)

        with open('chunk_mapping.tar.xz', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        tar = tarfile.open('chunk_mapping.tar.xz', 'r:xz')
        tar.extractall()
        tar.close()

        with open('chunk_mapping.etag', 'w') as f:
            f.write(r.headers['ETag'])


def generate(patch):
    '''
    This function generates ...
    '''
    mapping = {}

    download_mapping()

    paths = []
    for diff in whatthepatch.parse_patch(patch.decode('utf-8')):
        # Get old and new path, for files that have been renamed.
        path = diff.header.new_path[2:] if diff.header.new_path.startswith('b/') else diff.header.new_path

        # If the diff doesn't contain any changes, we skip it.
        if diff.changes is None:
            continue

        # If the file is not a source file, we skip it (as we already know
        # we have no coverage information for it).
        if not coverage_supported(path):
            continue

        paths.append(path)

    with sqlite3.connect('chunk_mapping.db') as conn:
        c = conn.cursor()
        for path in paths:
            c.execute('SELECT chunk FROM files WHERE path=?', (path.encode('utf-8'),))
            mapping[path] = c.fetchall()

    return mapping
