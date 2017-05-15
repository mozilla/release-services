import click
import functools


def taskcluster_options(func):
    """
    Setup taskcluster CLI options
    """
    @click.option(
        '--taskcluster-secret',
        help='Taskcluster Secret path',
        envvar='TASKCLUSTER_SECRET',
    )
    @click.option(
        '--taskcluster-client-id',
        help='Taskcluster Client ID',
        envvar='TASKCLUSTER_CLIENT_ID',
    )
    @click.option(
        '--taskcluster-access-token',
        help='Taskcluster Access token',
        envvar='TASKCLUSTER_ACCESS_TOKEN'
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
