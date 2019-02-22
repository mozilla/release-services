# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import urllib
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

import click

import cli_common.cli
import cli_common.log

log = cli_common.log.get_logger(__name__)

AUTH_URL = 'https://tools.taskcluster.net/auth/clients/new'


class TaskclusterSigninServer(BaseHTTPRequestHandler):
    '''
    Wait for Taskcluster response with temporary credentials
    '''

    def do_GET(self):

        # Load credentials provided by Taskcluster from URL
        assert self.path.startswith('/?')
        credentials = dict(urllib.parse.parse_qsl(self.path[2:]))
        assert 'clientId' in credentials, 'Missing clientId'
        assert 'accessToken' in credentials, 'Missing accessToken'

        # Save in local config
        self.server.taskcluster_credentials = credentials

        # Send text response to browser
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Credentials saved. You can close this page.')


@click.command(
    help='Retrieves Taskcluster credentials to use on your local environment'
)
@click.option(
    '--server-port',
    type=int,
    required=True,
    default=9000,
)
@click.pass_context
def cmd(ctx, server_port):
    config = ctx.obj['config']
    if 'common' in config and 'taskcluster_client_id' in config['common']:
        click.secho('Taskcluster credentials, already set, they will be erased !', fg='red')

    # Start webserver
    httpd = HTTPServer(('localhost', server_port), TaskclusterSigninServer)
    httpd.taskcluster_credentials = {}

    callback_url = 'http://localhost:{}'.format(server_port)

    # Redirect user to url
    params = {
        'name': 'mozilla-release-services',
        'description': 'Local development credentials for Mozilla Release Services',
        'scope': [],
        'expires': '1 month',
        'callback_url': callback_url,
    }
    client_url = '{}?{}'.format(AUTH_URL, urllib.parse.urlencode(params))
    click.secho('Please use this url: {}'.format(client_url), fg='blue')

    # Wait for credentials
    click.echo('Waiting for HTTP request...')
    while not httpd.taskcluster_credentials:
        httpd.handle_request()

    # Write credentials
    config.write_user_config({
        'common': {
            'taskcluster_client_id': httpd.taskcluster_credentials['clientId'],
            'taskcluster_access_token': httpd.taskcluster_credentials['accessToken'],
        }
    })
    click.secho('Taskcluster credentials saved !', fg='green')
