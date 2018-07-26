# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from cli_common import log
from shipit_code_coverage_backend.services.active_data import ActiveDataCoverage
from shipit_code_coverage_backend.v2.base import active_data, NoResults

logger = log.get_logger(__name__)


def coverage_diff(changeset):
    '''
    List all the coverage changes introduced by a diff
    '''

    print('DIFF', changeset)

    # Load revision from MC
    rev = active_data.get_changeset(changeset)

    from pprint import pprint
    pprint(rev)

    files = rev['changeset']['files']
    push = rev['push']['id']
    logger.info('Looking up coverage', files=files, push=push)

    # Load all the other commits on this push, above this changeset
    # and for these files
    query = {
        'query': {
            'bool': {

                # Files intersection
                'should': [
                    { 'match': {'changeset.files': f}}
                    for f in files
                ],

                'must': [
                    # After our commit
                    {'range': {
                        'index': {'gt': rev['index']},
                    }},

                    # Same push and repo
                    {'match': {'push.id': push}},
                    {'match': {'branch.name': rev['branch']['name']}},
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
        others = None

    if others:
        for o in others['hits']['hits']:
            print('-' * 40)
            print(o['_source']['changeset']['description'])

    # Load coverage for these files, on this push
    # TODO: aggregate covered/uncovered
    filters = [
        # Filter by files
        {'terms': {ActiveDataCoverage.FIELD_FILENAME: files}},

        # Filter by push
        {'term': {ActiveDataCoverage.FIELD_PUSH: push}},
    ]
    query = ActiveDataCoverage.base_query(filters)
    #query.update({
    #    'size': 0,
    #    'aggs': {
    #        'files': {
    #            'terms': {'field': ActiveDataCoverage.FIELD_FILENAME},

    #            'aggs': {
    #                'covered': {
    #    		"scripted_metric": {
    #    		    "init_script" : "params._agg.covered = []",
    #    		    #"map_script" : "params._agg.covered.addAll(doc.source.file.covered)",
    #    		    "map_script" : "params._agg.covered.add(42)",
    #    		    "reduce_script" : "Set out = new Set();for (a in params._aggs) { out.addAll(a); } return out.toArray();",
    #    		}
    #    	    }
    #            }
    #        },
    #    },
    #})
    #query['size'] = 100

    out = active_data.search('coverage_files_push', query, timeout=100)

    from pprint import pprint
    pprint(out)
    return {}
