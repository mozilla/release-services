# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from flask_restplus import Resource


class App:
    pass


def init_app(app):

    clobberer = App()

    @app.api.route('/buildbot')
    class Buildbot(Resource):

        def get(self):
            return {'hello': 'world'}

        def post(self):
            return {'hello': 'world'}

    @app.api.route('/taskcluster')
    class Taskcluster(Resource):

        def get(self):
            return {'hello': 'world'}

        def post(self):
            return {'hello': 'world'}


    return clobberer
