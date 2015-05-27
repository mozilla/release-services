# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import current_app
from flask import request


class Layout(object):

    def __init__(self, app):
        self.extra_head_content = []

        @app.context_processor
        def _context_processor():
            if request.blueprint:
                blueprint = current_app.blueprints[request.blueprint]
            else:
                blueprint = current_app.blueprints['base']
            return {
                'blueprint': blueprint,
                'layout_extra_head_content': self.extra_head_content,
            }

    def add_head_content(self, content):
        """
        Add ``content`` to the ``<head>`` element in every page.
        """
        self.extra_head_content.append(content)

    def add_script(self, url):
        """
        Add a ``<script>`` tag pointing to ``url`` to the head of every page.
        """
        self.add_head_content("""<script src="%s" type="text/javascript"></script>""" % url)


def init_app(app):
    app.layout = Layout(app)
