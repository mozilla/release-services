# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import StringIO
import logging
import os
import pkg_resources
import shutil
import sys

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import render_template
from flask import send_from_directory
from relengapi.lib import subcommands
from sphinx.websupport import WebSupport
from sphinx.websupport.errors import DocumentNotFoundError

logger = logging.getLogger(__name__)

bp = Blueprint('docs', __name__,
               template_folder='templates')
bp.root_widget_template('docs_root_widget.html', priority=100)


def get_builddir():
    if 'DOCS_BUILD_DIR' in current_app.config:
        return current_app.config['DOCS_BUILD_DIR']
    relengapi_dist = pkg_resources.working_set.find(
        pkg_resources.Requirement.parse('relengapi'))
    return os.path.join(
        pkg_resources.resource_filename(relengapi_dist.as_requirement(), ''),
        'docs_build_dir')


def get_support(force=False, quiet=False):
    if not hasattr(current_app, 'docs_websupport') or force:
        builddir = get_builddir()
        # this is where files installed by setup.py's data_files go..
        srcdir = os.path.join(sys.prefix, 'relengapi-docs')
        kwargs = {}
        if quiet:
            kwargs['status'] = StringIO.StringIO()
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
                                       help='make a built version of the '
                                            'sphinx documentation')
        parser.add_argument("--quiet", action='store_true',
                            help="Quiet output")
        parser.add_argument("--development", '-d', action='store_true',
                            help="""Build docs in development mode.  Use this if the
                                 relengapi packages are installed with `setup.py
                                 develop` or `pip install -e`""")
        return parser

    def copy_docs(self, src_root, dst_root):
        logger.info(
            "Copying documentation from {!r} to {!r}".format(src_root, dst_root))
        for src, dirs, files in os.walk(src_root):
            dst = src.replace(src_root, dst_root)
            if not os.path.isdir(dst):
                os.makedirs(dst)
            for f in files:
                shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))

    def run(self, parser, args):
        # always start with a fresh build dir
        builddir = get_builddir()
        if os.path.exists(builddir):
            shutil.rmtree(builddir)
        os.makedirs(builddir)

        # force get_support to create a fresh WebSupport object since it
        # creates some directories in its constructor, which may have been
        # called before the builddir was erased.
        support = get_support(force=True, quiet=args.quiet)

        # if we're in development mode, go find and merge all of the `docs`
        # directories from any distribution with a relengapi blueprint into the
        # srcdir.  This is the same operation that 'setup.py install' would do,
        # but that doesn't happen automatically on 'setup.py develop'.
        if args.development:
            dists = sorted(set(bp.dist for bp in current_app.relengapi_blueprints.itervalues()))
            for dist in dists:
                docs_dir = os.path.join(dist.location, 'docs')
                if not os.path.isdir(docs_dir):
                    # not covered because we may not have such a dist installed
                    continue  # pragma: no cover
                self.copy_docs(docs_dir, support.srcdir)

        # actually build the docs
        support.build()
