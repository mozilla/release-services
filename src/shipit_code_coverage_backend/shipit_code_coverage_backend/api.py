# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio

from rq import Queue

from cli_common.phabricator import PhabricatorAPI
from cli_common.phabricator import revision_exists_on_central
from shipit_code_coverage_backend import coverage
from shipit_code_coverage_backend import coverage_by_changeset_impl
from shipit_code_coverage_backend import coverage_for_file_impl
from shipit_code_coverage_backend import coverage_summary_by_changeset_impl
from shipit_code_coverage_backend import secrets
from shipit_code_coverage_backend.worker import conn

q = Queue(connection=conn)


def coverage_for_file(changeset, path):
    changeset = changeset[:12]
    try:
        return asyncio.get_event_loop().run_until_complete(coverage_for_file_impl.generate(changeset, path))
    except Exception as e:
        return {
            'error': str(e)
        }, 500


def coverage_by_changeset_job(changeset):
    return asyncio.get_event_loop().run_until_complete(coverage_by_changeset_impl.generate(changeset))


def coverage_by_changeset(changeset):
    changeset = changeset[:12]

    job = q.fetch_job(changeset)

    if job is None:
        RESULT_TTL = 2 * 24 * 60 * 60
        job = q.enqueue(
            coverage_by_changeset_job,
            changeset,
            job_id=changeset,
            result_ttl=RESULT_TTL
        )

    if job.result is not None:
        return job.result, 200

    if job.exc_info is not None:
        return {
            'error': str(job.exc_info)
        }, 500

    return '', 202


def coverage_summary_by_changeset(changeset):
    result, code = coverage_by_changeset(changeset)
    if code != 200:
        return result, code
    else:
        return coverage_summary_by_changeset_impl.generate(result), 200


def coverage_supported_extensions():
    return coverage.COVERAGE_EXTENSIONS


def coverage_latest():
    return asyncio.get_event_loop().run_until_complete(coverage.get_latest_build_info())


def phabricator_base_revision_from_phid(revision_phid):
    try:
        phabricator = PhabricatorAPI(secrets.PHABRICATOR_TOKEN)
        for diff in phabricator.search_diffs(revision_phid=revision_phid):
            revision = diff['baseRevision']
            if revision and revision_exists_on_central(revision):
                return {'revision': revision}, 200
        return {'error': 'Base revision not found.'}, 404
    except Exception as e:
        return {
            'error': str(e),
            'error_code': getattr(e, 'error_code', 'unknown')
        }, 500
