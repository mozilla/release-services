# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from relengapi import subcommands
from flask import Blueprint
from flask import jsonify
from flask import abort
from flask import current_app
from flask import render_template
from flask import send_from_directory
from sphinx.websupport import WebSupport
from sphinx.websupport.errors import DocumentNotFoundError

docsdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
staticdir = os.path.join(docsdir, 'build', 'static')
support = WebSupport(
    srcdir=os.path.join(docsdir, 'src'),
    builddir=os.path.join(docsdir, 'build'),
    staticroot='/docs/static',
    docroot='/docs')

bp = Blueprint('docs', __name__,
               template_folder='templates',
               static_folder=staticdir)


@bp.route('/', defaults={'docname': 'index'})
@bp.route('/<path:docname>')
def doc(docname):
    try:
        doc = support.get_document(docname.strip('/'))
    except DocumentNotFoundError:
        abort(404)
    return render_template('doc.html', document=doc)


@bp.route('/websupport-custom.css')
def websupport_custom():
    return send_from_directory(docsdir, 'websupport-custom.css')

# TODO:


def api_info(docname):
    rv = []
    vfs = current_app.view_functions
    for map in current_app.url_map.iter_rules():
        func = vfs[map.endpoint]
        if func.__doc__ and func.__doc__.startswith('API:'):
            rv.append((map.rule, func.__doc__))
    return jsonify(rv)


class CreateDBSubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('build-docs',
                                       help='make a built version of the sphinx documentation')
        return parser

    def run(self, parser, args):
        support.build()
