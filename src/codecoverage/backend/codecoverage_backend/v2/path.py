# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from cli_common import log
from codecoverage_backend.services.active_data import ActiveDataCoverage
from codecoverage_backend.v2.base import active_data

logger = log.get_logger(__name__)

# This is a "painless" ES script, that is used by the aggregation
# to build coverage per path.
# It reduces a path to its top folder or filename
# AFTER a specified prefix length (the searched path)
GROUP_BY_FOLDER = '''
String sub = _value.substring({path_len});
int index = sub.indexOf('/');
if (index == -1)
  return _value;
return _value.substring(0, {path_len} + index + 1);
'''


def coverage_paths(path, changeset):
    '''
    Aggregate coverage percent data from ES for a given path and changeset
    The output will be a list of typed path (directory|file) and its total coverage
    '''
    assert not path.startswith('/'), 'No absolute path'

    filters = [
        # Filter by changeset
        {'term': {ActiveDataCoverage.FIELD_CHANGESET: changeset}},

        # Filename must start with specified path
        {'prefix': {ActiveDataCoverage.FIELD_FILENAME: path}},
    ]
    excludes = [
        # Remove weird rust macros
        {'wildcard': {ActiveDataCoverage.FIELD_FILENAME: '<* macros>'}},

        # Remove weird NONE
        {'term': {ActiveDataCoverage.FIELD_FILENAME: 'NONE'}},
    ]

    query = ActiveDataCoverage.base_query(filters, excludes)
    query.update({
        'aggs': {
            # Group by filename
            'coverage': {
                'terms': {
                    'field': ActiveDataCoverage.FIELD_FILENAME,
                    'script': {
                        'source': GROUP_BY_FOLDER.format(path_len=len(path)),
                        'lang': 'painless',
                    },

                    # Sort by filename
                    'order': {'_key': 'asc'},

                    # Should be enough to cover every folder in one query
                    # Biggest sa-central folder has 3600+ sub elements
                    'size': 5000,
                },

                # For each filename, average the coverage percent
                # over all the tests
                'aggs': {
                    'percent': {
                        'avg': {
                            'field': ActiveDataCoverage.FIELD_TOTAL_PERCENT,
                        }
                    }
                }
            }
        },

        # No hits please, that's just extra load
        'size': 0,
    })

    out = active_data.search('coverage_paths', query)
    return [
        {
            'path': item['key'],
            'coverage': item['percent']['value'],
            'nb': item['doc_count'],
            'type': item['key'].endswith('/') and 'directory' or 'file'
        }
        for item in out['aggregations']['coverage']['buckets']
    ]
