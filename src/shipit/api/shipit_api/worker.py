# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import json
import os
import pathlib
import shutil
import tempfile

import flask

import cli_common.log
import cli_common.pulse
import cli_common.taskcluster
import shipit_api.config

logger = cli_common.log.get_logger(__name__)
temporary_dir = tempfile.gettempdir()
product_details_dir_name = 'product-details'
product_details_dir = pathlib.Path(temporary_dir, product_details_dir_name)


def generate_product_details(product_details_dir, breakpoint_version):
    # TODO: we need to migrate current code that generates from cli.py
    pass


def run_check(*arg, **kw):
    return cli_common.utils.retry(lambda: cli_common.command.run_check(*arg, **kw))


async def rebuild_product_details(channel, body, envelope, properties):
    '''Rebuild product details.
    '''
    body = json.loads(body.decode('utf-8'))

    secrets = cli_common.taskcluster.get_secrets(
        os.environ['TASKCLUSTER_SECRET'],
        shipit_api.config.PROJECT_NAME,
        required=(
            'PRODUCT_DETAILS_URL',
        ),
        taskcluster_client_id=['TASKCLUSTER_CLIENT_ID'],
        taskcluster_access_token=os.environ['TASKCLUSTER_ACCESS_TOKEN'],
    )

    product_details_url = secrets['PRODUCT_DETAILS_URL']

    # Sometimes we want to work from a clear working copy
    if body.get('clean_working_copy') and product_details_dir.exists():
        shutil.rmtree(product_details_dir)

    # Checkout product details or pull from already existing checkout
    if product_details_dir.exists():
        run_check(['git', 'pull'], cwd=product_details_dir)
    else:
        run_check(['git', 'clone', product_details_url, product_details_dir_name], cwd=temporary_dir)

    # TODO:
    # if breakpoint_version is not provided we should figure it out from product details
    # and if we can not figure it out we should use shipit_api.config.BREAKPOINT_VERSION
    # breakpoint_version should always be higher then shipit_api.config.BREAKPOINT_VERSION
    breakpoint_version = body.get('breakpoint_version', secrets.get('BREAKPOINT_VERSION'))

    # Generate product details
    generate_product_details(product_details_dir, breakpoint_version)

    # Add, commit and push changes
    run_check(['git', 'add', '.'], cwd=product_details_dir)
    # TODO: we need a better commmit message, maybe mention what triggered this update
    commit_message = 'Updating product details'
    run_check(['git', 'commit', '-m', commit_message], cwd=product_details_dir)
    run_check(['git', 'push'], cwd=product_details_dir)

    # TODO: maybe check that commit landed to github


def cmd(app):
    queue = 'exchange/{}/{}'.format(
        flask.current_app.config['PULSE_USER'],
        shipit_api.config.PROJECT_NAME,
    )
    rebuild_product_details_consumer = cli_common.pulse.create_consumer(
        app.config['PULSE_USER'],
        app.config['PULSE_PASSWORD'],
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
