# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import io
import json
import os
import pathlib
import shutil
import tempfile

import aiohttp
import asyncio
import click

JSON_FILES = []



def coroutine(f):
    f = asyncio.coroutine(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))
    return functools.update_wrapper(wrapper, f)


async def download_json_file(session, url, file_):
    click.echo(f'=> Downloading {url}')
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()

        content = await response.text()

        file_dir = os.path.dirname(file_)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        with io.open(file_, 'w+') as f:
            f.write(content)
        click.echo(f'=> Downloaded to {file_}')

        return (url, file_)


@click.command(name='upload-product-details')
@click.option(
    '--download-dir',
    required=True,
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        readable=True,
    ),
)
@click.option(
    '--shipit-url',
    default='https://ship-it.mozilla.org',
)
@coroutine
async def download_product_details(shipit_url, download_dir):

    if os.path.isdir(download_dir):
        shutil.rmtree(download_dir)
        os.makedirs(download_dir)

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{shipit_url}/json_exports.json') as response:
            if response.status != 200:
                response.raise_for_status()
            json_paths = await response.json()

        await asyncio.gather(*[
            download_json_file(
                session,
                f'{shipit_url}{json_path}',
                f'{download_dir}{json_path}',
            )
            for json_path in json_paths
        ])

    click.echo('All files were downloaded successfully!')


@click.command(name='upload-product-details')
def upload_product_details():

    # get release data:
    # 1. from static blobs until certain version
    # 2. and from the database from and including certain version

    # create temp directory where generated files will be
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = pathlib.Path(temp_dir)

        # go over all files and call their content factories
        for (json_file, get_content) in JSON_FILES:
            json_path = temp_dir.joinpath(json_file)

            # we must ensure that all needed folders
            os.makedirs(os.path.direname(json_path))

            # write content into json file
            with json_path.open() as f:
                f.write(get_content())

        # TODO: sync to s3
