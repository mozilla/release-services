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


def rebuild_product_details(default_git_repo_url,
                            default_folder_in_repo,
                            default_channel,
                            default_breakpoint_version,
                            default_clean_working_copy,
                            ):
    '''Rebuild product details.
    '''
    logger.debug('Rebuilding product details')

    taskcluster_secret = os.environ['TASKCLUSTER_SECRET']
    taskcluster_client_id = os.environ['TASKCLUSTER_CLIENT_ID']
    taskcluster_access_token = os.environ['TASKCLUSTER_ACCESS_TOKEN']

    logger.debug(f'Fetching secrets from {taskcluster_secret}')
    secrets = cli_common.taskcluster.get_secrets(
        taskcluster_secret,
        shipit_api.config.PROJECT_NAME,
        taskcluster_client_id=taskcluster_client_id,
        taskcluster_access_token=taskcluster_access_token,
    )

    git_repo_url = secrets.get('PRODUCT_DETAILS_GIT_REPO_URL', default_git_repo_url)
    default_channel = default_channel or secrets.get('APP_CHANNEL', os.environ.get('APP_CHANNEL', 'master'))
    default_breakpoint_version = secrets.get('BREAKPOINT_VERSION', default_breakpoint_version)

    async def rebuild_product_details_async(channel, body, envelope, properties):
        try:
            body = json.loads(body.decode('utf-8'))

            logger.debug('Get rebuild parameters from request payload', body=body)
            breakpoint_version = body.get('breakpoint_version', default_breakpoint_version)
            clean_working_copy = body.get('clean_working_copy', default_clean_working_copy)
            channel_ = body.get('channel', default_channel)
            folder_in_repo = body.get('folder_in_repo', default_folder_in_repo)

            logger.debug('Rebuild parameters',
                         channel=channel_,
                         folder_in_repo=folder_in_repo,
                         breakpoint_version=breakpoint_version,
                         clean_working_copy=clean_working_copy,
                         )
            if None in (channel_, git_repo_url, folder_in_repo):
                raise click.ClickException('One of the rebuild product details parameters is not set correctly.')

            await shipit_api.product_details.rebuild(flask.current_app.db.session,
                                                     channel_,
                                                     git_repo_url,
                                                     folder_in_repo,
                                                     breakpoint_version,
                                                     clean_working_copy,
                                                     )
            logger.debug('Product details rebuilt')

        finally:
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
            logger.debug('Marked pulse message as acknowledged.')

    return rebuild_product_details_async


@click.command()
@click.option(
    '--git-repo-url',
    type=str,
    required=False,
    default=None,
)
@click.option(
    '--folder-in-repo',
    type=str,
    required=True,
    default='public/',
)
@click.option(
    '--channel',
    type=click.Choice([
        'master',
        'testing',
        'staging',
        'production',
    ]),
    default=None,
)
@click.option(
    '--breakpoint-version',
    default=shipit_api.config.BREAKPOINT_VERSION,
    type=int,
)
@click.option(
    '--clean-working-copy',
    is_flag=True,
    default=True,
)
@flask.cli.with_appcontext
def cmd(git_repo_url,
        folder_in_repo,
        channel,
        breakpoint_version,
        clean_working_copy,
        ):
    pulse_user = flask.current_app.config['PULSE_USER']
    pulse_pass = flask.current_app.config['PULSE_PASSWORD']
    exchange = f'exchange/{pulse_user}/{shipit_api.config.PROJECT_NAME}'
    rebuild_product_details_consumer = cli_common.pulse.create_consumer(
        pulse_user,
        pulse_pass,
        exchange,
        shipit_api.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
        rebuild_product_details(git_repo_url,
                                folder_in_repo,
                                channel,
                                breakpoint_version,
                                clean_working_copy,
                                ),
    )
    logger.info(
        'Listening for new messages on',
        exchange=exchange,
        route=shipit_api.config.PULSE_ROUTE_REBUILD_PRODUCT_DETAILS,
    )
    cli_common.pulse.run_consumer(asyncio.gather(*[
        rebuild_product_details_consumer,
    ]))
