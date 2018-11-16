# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import functools
import io
import json
import os
import shutil
import typing

import aiohttp
import click
import mohawk
import requests
import sqlalchemy
import sqlalchemy.orm

import shipit_api.product_details


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
async def download_product_details(shipit_url: str, download_dir: str):

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


@click.command(name='rebuild-product-details')
@click.option(
    '--database-url',
    type=int,
)
@click.option(
    '--breakpoint-version',
    default=None,
    type=int,
)
@click.option(
    '--clean-working-copy',
    is_flag=True,
)
def rebuild_product_details(database_url: str,
                            breakpoint_version: typing.Optional[int],
                            clean_working_copy: bool,
                            ):
    engine = sqlalchemy.create_engine(database_url)
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    shipit_api.product_details.rebuild(session, breakpoint_version, clean_working_copy)


def get_taskcluster_headers(request_url,
                            method,
                            content,
                            taskcluster_client_id,
                            taskcluster_access_token,
                            ):
    hawk = mohawk.Sender(
        {
            'id': taskcluster_client_id,
            'key': taskcluster_access_token,
            'algorithm': 'sha256',
        },
        request_url,
        method,
        content,
        content_type='application/json',
    )
    return {
        'Authorization': hawk.request_header,
        'Content-Type': 'application/json',
    }


@click.command(name='shipit-v1-sync')
@click.option(
    '--ldap-username',
    help='LDAP username',
    required=True,
    prompt=True,
)
@click.option(
    '--ldap-password',
    help='LDAP password',
    required=True,
    prompt=True,
    hide_input=True,
)
@click.option(
    '--taskcluster-client-id',
    help='Taskcluster Client ID',
    required=True,
    prompt=True,
)
@click.option(
    '--taskcluster-access-token',
    help='Taskcluster Access token',
    required=True,
    prompt=True,
    hide_input=True,
)
@click.option(
    '--api-from',
    default='https://ship-it.mozilla.org',
)
@click.option(
    '--api-to',
    required=True,
)
def v1_sync(ldap_username,
            ldap_password,
            taskcluster_client_id,
            taskcluster_access_token,
            api_from,
            api_to,
            ):

    s = requests.Session()
    s.auth = (ldap_username, ldap_password)

    click.echo('Fetching release list...', nl=False)
    req = s.get(f'{api_from}/releases')
    releases = req.json()['releases']
    click.echo(click.style('OK', fg='green'))

    releases_json = []

    with click.progressbar(releases, label='Fetching release data') as releases:
        for release in releases:
            r = s.get(f'{api_from}/releases/{release}')
            releases_json.append(r.json())

    click.echo('Syncing release list...', nl=False)
    headers = get_taskcluster_headers(
        f'{api_to}/sync',
        'post',
        json.dumps(releases_json),
        taskcluster_client_id,
        taskcluster_access_token,
    )
    r = requests.post(
        f'{api_to}/sync',
        headers=headers,
        verify=False,
        json=releases_json,
    )
    r.raise_for_status()
    click.echo(click.style('OK', fg='green'))
