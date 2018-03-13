# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from shipit_static_analysis.workflow import Workflow
from shipit_static_analysis.revisions import PhabricatorRevision, MozReviewRevision
from shipit_static_analysis.config import settings
from shipit_static_analysis.report import get_reporters
from shipit_static_analysis import config, stats
from cli_common.click import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from cli_common.log import get_logger
import click

logger = get_logger(__name__)


@click.command()
@taskcluster_options
@click.option(
    '--phabricator',
    envvar='PHABRICATOR',
)
@click.option(
    '--mozreview',
    envvar='MOZREVIEW',
)
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
@stats.api.timer('runtime.analysis')
def main(phabricator,
         mozreview,
         cache_root,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    assert (phabricator is None) ^ (mozreview is None), \
        'Specify a phabricator XOR mozreview parameters'

    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          required=(
                              'APP_CHANNEL',
                              'REPORTERS',
                              'ANALYZERS',
                          ),
                          existing={
                              'APP_CHANNEL': 'development',
                              'REPORTERS': [],
                              'ANALYZERS': ['clang-tidy', ],
                          },
                          taskcluster_client_id=taskcluster_client_id,
                          taskcluster_access_token=taskcluster_access_token,
                          )

    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    # Setup settings before stats
    settings.setup(secrets['APP_CHANNEL'])

    # Setup statistics
    datadog_api_key = secrets.get('DATADOG_API_KEY')
    if datadog_api_key:
        stats.auth(datadog_api_key)

    # Load reporters
    reporters = get_reporters(
        secrets['REPORTERS'],
        taskcluster_client_id,
        taskcluster_access_token,
    )

    # Load revisions
    revisions = []
    if phabricator:
        # Only one phabricator revision at a time
        api = reporters.get('phabricator')
        assert api is not None, \
            'Cannot use a phabricator revision without a phabricator reporter'
        revisions.append(PhabricatorRevision(phabricator, api))
    if mozreview:
        # Multiple mozreview revisions are possible
        revisions += [
            MozReviewRevision(r)
            for r in mozreview.split(' ')
        ]

    w = Workflow(cache_root, reporters, secrets['ANALYZERS'])
    for revision in revisions:
        try:
            w.run(revision)
        except Exception as e:
            # Log errors to papertrail
            logger.error(
                'Static analysis failure',
                revision=revision,
                error=e,
            )

            # Then raise to mark task as erroneous
            raise


if __name__ == '__main__':
    main()
