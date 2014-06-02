# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from relengapi import subcommands
from pkg_resources import resource_filename
from flask import Blueprint
from flask import abort
from flask import current_app
from flask import render_template
from flask import send_from_directory
from sphinx.websupport import WebSupport
from sphinx.websupport.errors import DocumentNotFoundError
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('docs', __name__,
               template_folder='templates')
bp.root_widget_template('docs_root_widget.html', priority=100)


def get_support(**kwargs):
    if not hasattr(current_app._get_current_object(), 'docs_websupport'):
        srcdir = resource_filename(__name__, 'src')
        builddir = os.path.join(os.path.dirname(srcdir), 'build')
        builddir = current_app.config.get('DOCS_BUILD_DIR', builddir)
        current_app.docs_websupport = WebSupport(
            srcdir=srcdir,
            builddir=builddir,
            staticroot='/docs/static',
            docroot='/docs',
            **kwargs)
    return current_app.docs_websupport


@bp.record
def check_built(state):
    with state.app.app_context():
        support = get_support()
        if not os.path.exists(os.path.join(support.builddir, 'data', '.buildinfo')):
            if not state.app.config.get('TESTING'):  # pragma: no cover
                logger.warning("docs have not been built")


@bp.route('/', defaults={'docname': 'index'})
@bp.route('/<path:docname>')
def doc(docname):
    try:
        doc = get_support().get_document(docname.strip('/'))
    except DocumentNotFoundError:
        abort(404)
    return render_template('doc.html', document=doc)


@bp.route('/static', defaults={'path': ''})
@bp.route('/static/<path:path>')
def static(path):
    # the Blueprint's static_folder can't depend on app configuration, so we
    # just implement static files directly
    support = get_support()
    return send_from_directory(support.staticdir, path)


class BuildDocsSubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('build-docs',
                                       help='make a built version of the sphinx documentation')
        return parser

    def run(self, parser, args):
        get_support().build()
