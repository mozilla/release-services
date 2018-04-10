# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess

import livereload

HERE = os.path.dirname(__file__)

server = livereload.Server()
server.watch(
    os.path.join(HERE, '*.rst'),
    livereload.shell('make html'),
)
server.watch(
    os.path.join(HERE, '*', '*.rst'),
    livereload.shell('make html'),
)
server.watch(
    os.path.join(HERE, 'shipit_signoffs', '*.rst'),
    livereload.shell('make html'),
)

subprocess.call('make html', shell=True)

server.serve(
    port=os.environ.get('PORT', 5000),
    host=os.environ.get('HOST', 'localhost'),
    root=os.path.join(HERE, 'build/html'),
)
