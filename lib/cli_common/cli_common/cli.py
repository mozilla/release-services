# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools

import click


def taskcluster_options(func):
    '''
    Setup taskcluster CLI options
    '''
    @click.option(
        '--taskcluster-secret',
        help='Taskcluster Secret path',
        default='repo:github.com/mozilla-releng/services:branch:master',
        envvar='TASKCLUSTER_SECRET',
    )
    @click.option(
        '--taskcluster-client-id',
        help='Taskcluster Client ID',
        default=None,
        envvar='TASKCLUSTER_CLIENT_ID',
    )
    @click.option(
        '--taskcluster-access-token',
        help='Taskcluster Access token',
        default=None,
        envvar='TASKCLUSTER_ACCESS_TOKEN'
    )
    @click.pass_context
    @functools.wraps(func)
    def wrapper(context, *args, **kwargs):

        # Load credentials from available user config
        context.ensure_object(dict)
        config = context.obj.get('config')
        if config and 'taskcluster' in config:
            if kwargs['taskcluster_client_id'] is None:
                kwargs['taskcluster_client_id'] = config['taskcluster'].get('clientId')
            if kwargs['taskcluster_access_token'] is None:
                kwargs['taskcluster_access_token'] = config['taskcluster'].get('accessToken')

        return func(*args, **kwargs)
    return wrapper
