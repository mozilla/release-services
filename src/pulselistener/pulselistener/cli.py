# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import tempfile

import click

from cli_common.cli import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from pulselistener import config
from pulselistener.code_coverage import CodeCoverage
from pulselistener.code_review import CodeReview


@click.command()
@click.argument(
    'workflow',
    type=click.Choice(['code-review', 'code-coverage']),
    required=True,
)
@click.option(
    '--cache-root',
    required=False,
    help='Cache root, used to pull changesets',
    default=os.path.join(tempfile.gettempdir(), 'pulselistener'),
)
@taskcluster_options
def main(workflow,
         cache_root,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          required=(
                              'PULSE_USER',
                              'PULSE_PASSWORD',
                              'HOOKS',
                              'ADMINS',
                              'PHABRICATOR',
                              'repositories',
                          ),
                          existing=dict(
                              HOOKS=[],
                              ADMINS=['babadie@mozilla.com', 'mcastelluccio@mozilla.com'],
                              repositories=[]
                          ),
                          taskcluster_client_id=taskcluster_client_id,
                          taskcluster_access_token=taskcluster_access_token,
                          )

    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    workflow_classes = {
        'code-coverage': CodeCoverage,
        'code-review': CodeReview,
    }

    workflow = workflow_classes[workflow](
        secrets,
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
        cache_root=cache_root,
    )
    workflow.run()


if __name__ == '__main__':
    main()
