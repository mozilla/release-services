# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import json
import os

import click
import flask

import cli_common.log
import cli_common.pulse
import cli_common.taskcluster
import shipit_api.config

logger = cli_common.log.get_logger(__name__)


def generate_product_details(product_details_dir, breakpoint_version):
    # TODO: we need to migrate current code that generates from cli.py
    pass


async def rebuild_product_details(channel, body, envelope, properties):
    '''Rebuild product details.
    '''

    secrets = cli_common.taskcluster.get_secrets(
        os.environ['TASKCLUSTER_SECRET'],
        shipit_api.config.PROJECT_NAME,
        required=(
            'PRODUCT_DETAILS_GIT_REPO_URL',
        ),
        taskcluster_client_id=os.environ['TASKCLUSTER_CLIENT_ID'],
        taskcluster_access_token=os.environ['TASKCLUSTER_ACCESS_TOKEN'],
    )

    body = json.loads(body.decode('utf-8'))
    breakpoint_version = body.get('breakpoint_version', secrets.get('BREAKPOINT_VERSION'))
    clean_working_copy = body.get('clean_working_copy', False)

    shipit_api.product_details.rebuild(flask.current_app.db.session,
                                       secrets['PRODUCT_DETAILS_GIT_REPO_URL'],
                                       breakpoint_version,
                                       clean_working_copy,
                                       )


@click.command()
@flask.cli.with_appcontext
def cmd():
    pulse_user = flask.current_app.config['PULSE_USER']
    pulse_pass = flask.current_app.config['PULSE_PASSWORD']
    queue = f'exchange/{pulse_user}/{shipit_api.config.PROJECT_NAME}'
    rebuild_product_details_consumer = cli_common.pulse.create_consumer(
        pulse_user,
        pulse_pass,
        queue,
        shipit_api.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
        rebuild_product_details,
    )

    logger.info(
        'Listening for new messages on',
        queue=queue,
        route=shipit_api.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
    )

    cli_common.pulse.run_consumer(asyncio.gather(*[
        rebuild_product_details_consumer,
    ]))
