
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import json
import os


@click.command()
@click.option(
    '--taskcluster-secrets',
    envvar='TASKCLUSTER_SECRETS',
    default=None,
    required=False,
    )
def cmd(taskcluster_secrets,
        ):
    """A tool to be ran on each commit.
    """

    click.echo("1/4: Retriving secrets (${taskcluster_secrets})")

    if os.path.exists(taskcluster_secrets):
        with open(taskcluster_secrets) as f:
            taskcluster_secrets = json.load(f)
        # when taskcluster_secrets are provided with file make sure
    else:
        with open('/etc/hosts') as f:


    click.echo('2/4: Checking cache which application needs to be built')

    click.echo('3/4: Creating taskcluster tasks definitions (./tmp/tasks.json)')

    # TODO: create deployment options only in case of GITHUB_BASE_BRANCHk
    click.echo('4/4: Submitting taskcluster definitions to taskcluster')


if __name__ == "__main__":
    cmd()
