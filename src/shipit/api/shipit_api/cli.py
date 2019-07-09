# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import functools
import io
import json
import os
import typing

import aiohttp
import backoff
import click
import flask
import mohawk
import requests
import sqlalchemy
import sqlalchemy.orm

from shipit_api.models import Release
import shipit_api.product_details


def coroutine(f):
    '''A generic function to create a main asyncio loop
    '''
    coroutine_f = asyncio.coroutine(f)

    @functools.wraps(coroutine_f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine_f(*args, **kwargs))

    return wrapper


@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_time=60)
async def download_json_file(session, url, file_):
    click.echo(f'=> Downloading {url}')
    async with session.get(url) as response:
        response.raise_for_status()

        content = await response.json()

        file_dir = os.path.dirname(file_)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        with io.open(file_, 'w+') as f:
            f.write(json.dumps(content, sort_keys=True, indent=4))
        click.echo(f'=> Downloaded to {file_}')

        return (url, file_)


@click.command(name='upload-product-details')
@click.option(
    '--download-dir',
    required=True,
    type=click.Path(
        exists=False,
        file_okay=False,
        writable=True,
        readable=True,
    ),
)
@click.option(
    '--url',
    default='https://ship-it.mozilla.org',
)
@coroutine
async def download_product_details(url: str, download_dir: str):
    '''Download product details from `url` to `download_dir`.
    '''

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{url}/json_exports.json') as response:
            if response.status != 200:
                response.raise_for_status()
            paths = await response.json()

        await asyncio.gather(*[
            download_json_file(
                session,
                f'{url}{path}',
                f'{download_dir}{path}',
            )
            for path in paths
            if path.endswith('.json') and not os.path.exists(f'{download_dir}{path}')
        ])

    click.echo('All files were downloaded successfully!')


@click.command(name='rebuild-product-details')
@click.option(
    '--database-url',
    type=str,
    required=True,
    default='postgresql://127.0.0.1:9000/services',
)
@click.option(
    '--git-repo-url',
    type=str,
    required=True,
    default='https://github.com/mozilla-releng/product-details',
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
        'development',
        'master',
        'testing',
        'staging',
        'production',
    ]),
    required=True,
    default=os.environ.get('RELEASE_CHANNEL', 'master'),
)
@click.option(
    '--breakpoint-version',
    default=shipit_api.config.BREAKPOINT_VERSION,
    type=int,
)
@click.option(
    '--clean-working-copy',
    is_flag=True,
)
@coroutine
async def rebuild_product_details(database_url: str,
                                  git_repo_url: str,
                                  folder_in_repo: str,
                                  channel: str,
                                  breakpoint_version: typing.Optional[int] = None,
                                  clean_working_copy: bool = False,
                                  ):
    if channel == 'development':
        channel = 'master'
    engine = sqlalchemy.create_engine(database_url)
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    click.echo('Product details are building ...')
    await shipit_api.product_details.rebuild(session,
                                             channel,
                                             git_repo_url,
                                             folder_in_repo,
                                             breakpoint_version,
                                             clean_working_copy,
                                             )
    click.echo('Product details have been rebuilt')


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


@click.command(name='shipit-import')
@click.option(
    '--api-from',
    default='https://shipit-api.mozilla-releng.net',
)
@flask.cli.with_appcontext
def shipit_import(api_from):
    session = flask.current_app.db.session

    click.echo('Fetching release list...', nl=False)
    req = requests.get(f'{api_from}/releases?status=shipped,aborted,scheduled')
    releases = req.json()

    for release in releases:
        r = Release(
            product=release['product'],
            version=release['version'],
            branch=release['branch'],
            revision=release['revision'],
            build_number=release['build_number'],
            release_eta=release.get('release_eta'),
            partial_updates=release.get('partials'),
            status=release['status'],
        )
        r.created = release['created']
        r.completed = release['completed'] or release['created']
        session.add(r)
        session.commit()


@click.command(name='trigger-product-details')
@click.option(
    '--base-url',
    default='https://api.mozilla-releng.net',
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
def trigger_product_details(base_url: str,
                            taskcluster_client_id: str,
                            taskcluster_access_token: str,
                            ):
    data = '{}'
    url = f'{base_url}/product-details'

    click.echo(f'Triggering product details rebuild on {url} url ... ', nl=False)

    headers = get_taskcluster_headers(
        url,
        'post',
        data,
        taskcluster_client_id,
        taskcluster_access_token,
    )

    # skip ssl verification when working against development instances
    verify = not any(map(lambda x: x in base_url, ['localhost', '127.0.0.1']))

    r = requests.post(
        url,
        headers=headers,
        verify=verify,
        data=data,
    )

    r.raise_for_status()

    if r.json() != {'ok': 'ok'}:
        click.secho('ERROR: Something went wrong', fg='red')
        click.echo(f'  URL={url}')
        click.echo(f'  RESPONSE={r.content}')

    click.echo(click.style('Product details triggered successfully!', fg='green'))
