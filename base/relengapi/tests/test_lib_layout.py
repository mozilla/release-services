# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import render_template_string
from relengapi.lib.testing.context import TestContext

test_context = TestContext()


def render(app, client):
    @app.route('/test/layout')
    def test_layout():
        return render_template_string('{% extends "layout.html" %}')
    page = client.get('/test/layout')
    return page.data


@test_context
def test_add_script(app, client):
    app.layout.add_script('/some/url')
    exp = '<script src="/some/url" type="text/javascript"></script>'
    assert exp in render(app, client)


@test_context
def test_add_head_content(app, client):
    app.layout.add_head_content('CONTENT')
    assert 'CONTENT' in render(app, client)
