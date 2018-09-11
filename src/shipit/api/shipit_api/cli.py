# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import click
import mohawk

import requests


def get_taskcluster_headers(requests_url, method, content, taskcluster_client_id, taskcluster_access_token):
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
def shipit_v1_sync(ldap_username,
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
        api_to,
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
