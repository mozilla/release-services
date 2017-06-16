# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import json
import releng_clobberer


app = releng_clobberer.create_app()


@app.cli.command()
def taskcluster_cache():
    workertypes = releng_clobberer.cli.taskcluster_cache()
    click.echo(json.dumps(workertypes, indent=2, sort_keys=True))
