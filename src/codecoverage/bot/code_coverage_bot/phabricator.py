# -*- coding: utf-8 -*-

import re

from cli_common.log import get_logger
from cli_common.phabricator import PhabricatorAPI
from code_coverage_bot import hgmo
from code_coverage_bot.secrets import secrets

logger = get_logger(__name__)


class PhabricatorUploader(object):
    def __init__(self, repo_dir, revision):
        self.repo_dir = repo_dir
        self.revision = revision
        self.phabricator = PhabricatorAPI(secrets[secrets.PHABRICATOR_TOKEN], secrets[secrets.PHABRICATOR_URL])

    def _find_coverage(self, report, path):
        return next((sf['coverage'] for sf in report['source_files'] if sf['name'] == path), None)

    def _parse_revision_id(self, desc):
        PHABRICATOR_REVISION_REGEX = 'Differential Revision: https://phabricator.services.mozilla.com/D([0-9]+)'
        match = re.search(PHABRICATOR_REVISION_REGEX, desc)
        if not match:
            return None
        return int(match.group(1))

    def _build_coverage_map(self, annotate, coverage_record):
        # We can't use plain line numbers to map coverage data from the build changeset to the
        # changeset of interest, infact there could be intermediate changesets between them
        # modifying the same lines, thus displacing the line numbers.
        # In order to uniquely identify lines, and thus map coverage data, we use the annotate
        # data. The line number and changeset where a line was introduced are unique, so whenever
        # they match in the annotate data of the two changesets, we can be sure that it is the
        # same line.
        coverage_map = {}

        for data in annotate:
            # The line number at the build changeset.
            # Line numbers start from 1 in the annotate data, from 0 in the coverage data.
            lineno = data['lineno'] - 1
            # The line number when it was introduced.
            orig_line = data['targetline']
            # The changeset when it was introduced.
            orig_changeset = data['node']

            if lineno < len(coverage_record):
                key = '{}-{}'.format(orig_changeset, orig_line)
                coverage_map[key] = coverage_record[lineno]

        return coverage_map

    def _apply_coverage_map(self, annotate, coverage_map):
        phab_coverage_data = ''

        for data in annotate:
            # The line number when it was introduced.
            orig_line = data['targetline']
            # The changeset when it was introduced.
            orig_changeset = data['node']

            key = '{}-{}'.format(orig_changeset, orig_line)
            if key in coverage_map:
                count = coverage_map[key]
                if count is None:
                    # A non-executable line.
                    phab_coverage_data += 'N'
                elif count > 0:
                    phab_coverage_data += 'C'
                else:
                    phab_coverage_data += 'U'
            else:
                # We couldn't find the original changeset-original line in the annotate data for the build changeset,
                # this means that this line has been overwritten by another changeset.
                phab_coverage_data += 'X'

        return phab_coverage_data

    def generate(self, report):
        results = {}

        with hgmo.HGMO(self.repo_dir) as hgmo_server:
            changesets = hgmo_server.get_push_changesets(self.revision)

            for changeset in changesets:
                # Retrieve the revision ID for this changeset.
                revision_id = self._parse_revision_id(changeset['desc'])
                if revision_id is None:
                    continue

                results[revision_id] = {}

                # For each file...
                for path in changeset['files']:
                    # Retrieve the coverage data.
                    coverage_record = self._find_coverage(report, path)
                    if coverage_record is None:
                        continue

                    # Retrieve the annotate data for the build changeset.
                    build_annotate = hgmo_server.get_annotate(self.revision, path)
                    if build_annotate is None:
                        # This means the file has been removed by another changeset, but if this is the
                        # case, then we shouldn't have a coverage record and so we should have *continue*d
                        # earlier.
                        assert False, 'Failure to retrieve annotate data for the build changeset'

                    # Build the coverage map from the annotate data and the coverage data of the build changeset.
                    coverage_map = self._build_coverage_map(build_annotate, coverage_record)

                    # Retrieve the annotate data for the changeset of interest.
                    annotate = hgmo_server.get_annotate(changeset['node'], path)
                    if annotate is None:
                        assert False, 'Failure to retrieve annotate data for the changeset of interest'

                    # Apply the coverage map on the annotate data of the changeset of interest.
                    results[revision_id][path] = self._apply_coverage_map(annotate, coverage_map)

        return results

    def upload(self, report):
        results = self.generate(report)

        for revision_id, coverage in results.items():
            # TODO: Actually upload coverage data to Phabricator.
            pass
