# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import itertools

from cli_common import log
from shipit_code_coverage_backend.services.active_data import ActiveDataCoverage
from shipit_code_coverage_backend.v2.base import NoResults
from shipit_code_coverage_backend.v2.base import active_data

logger = log.get_logger(__name__)


def coverage_in_push(files, push):
    '''
    Load coverage for several files, on a specific push
    Aggregate covered lines directly through ES "painless"
    '''
    assert isinstance(files, (list, tuple))
    assert isinstance(push, int)

    filters = [
        # Filter by files
        {'terms': {ActiveDataCoverage.FIELD_FILENAME: files}},

        # Filter by push
        {'term': {ActiveDataCoverage.FIELD_PUSH: push}},
    ]
    query = ActiveDataCoverage.base_query(filters)
    query.update({
        'size': 0,
        'aggs': {
            'files': {
                'terms': {'field': ActiveDataCoverage.FIELD_FILENAME},

                'aggs': {
                    'covered': {
                        'scripted_metric': {
                            'init_script': 'params._agg.covered = []',

                            # Merge all the covered lines, per ES shard
                            'map_script': "params._agg.covered.addAll(doc['source.file.covered.~n~'])",

                            # Make a list with all items per shard
                            'combine_script': 'return params._agg.covered.stream().collect(Collectors.toList())',

                            # Merge all shards lists into a sorted set per file (top aggregation)
                            'reduce_script': 'return params._aggs.stream().flatMap(Collection::stream).sorted().distinct().collect(Collectors.toList())'
                        }
                    }
                }
            },
        },
    })
    out = active_data.search('coverage_files_push', query, timeout=100)

    return {
        bucket['key']: list(map(int, bucket['covered']['value']))
        for bucket in out['aggregations']['files']['buckets']
    }


def changes_on_files(files, push, revision_index, branch_name):
    '''
    List all the operations that happened on some files, in a push
    '''
    assert isinstance(files, (list, tuple))
    assert isinstance(push, int)
    query = {
        'query': {
            'bool': {

                # Files intersection
                'should': [
                    {'match': {'changeset.files': f}}
                    for f in files
                ],

                'must': [
                    # After our commit
                    {'range': {
                        'index': {'gt': revision_index},
                    }},

                    # Same push and repo
                    {'match': {'push.id': push}},
                    {'match': {'branch.name': branch_name}},
                ]
            }
        },

        # Only load moves
        '_source': ['changeset.moves', 'changeset.description'],

        # Probably should use scan/scroll
        'size': 100,
    }
    try:
        others = active_data.search('commits_above', body=query, index='repo')
    except NoResults:
        return {}

    # Group by files, with only our interesting files
    return {
        filename: [
            move['changes']
            for other in others['hits']['hits']
            for move in other['_source']['changeset']['moves']
            if move['new']['name'].endswith(filename) or move['old']['name'].endswith(filename)
        ]
        for filename in files
    }


def rewind(all_changes, original_lines):

    # TODO: move offsets calc in changes_on_files ?
    offsets = {}
    for changes in all_changes:
        for change in changes:
            if change['line'] not in offsets:
                offsets[change['line']] = 0

            offsets[change['line']] += change['action'] == '+' and 1 or -1

    # Apply the sum of all changes above the line to each line
    return {
        line: line + sum([
            offsets.get(i, 0)
            for i in range(1, line)
        ])
        for line in original_lines
    }


def coverage_diff(changeset):
    '''
    List all the coverage changes introduced by a diff
    '''
    # Load revision from MC
    rev = active_data.get_changeset(changeset)
    files = rev['changeset']['files']
    push = rev['push']['id']
    logger.info('Looking up coverage', files=files, push=push)

    # Get the lines affected by the patch, per files
    lines = {
        filename: set(itertools.chain(*[
            [c['line'] for c in move['changes']]
            for move in rev['changeset']['moves']
            if move['new']['name'].endswith(filename) or move['old']['name'].endswith(filename)
        ]))
        for filename in files
    }

    # Load all the other commits on this push, above this changeset
    # and for these files
    changes = changes_on_files(files, push, rev['index'], rev['branch']['name'])

    # Get final coverage on these files, for this push
    coverage = coverage_in_push(files, push)

    # Rewind the lines covered by unapplying every change
    out = {}
    for filename in files:

        file_changes = changes.get(filename)
        if file_changes is None:
            logger.warn('Missing changes', filename=filename)
            continue

        file_lines = rewind(file_changes, lines.get(filename))

        file_coverage = coverage.get(filename)
        out[filename] = [
            {
                'line': original_line,
                'covered': final_line in file_coverage
            }
            for original_line, final_line in file_lines.items()
        ]

    return out
