# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import shutil
import StringIO
from relengapi import subcommands
import pkg_resources
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


def get_basebuilddir():
    if 'DOCS_BUILD_DIR' in current_app.config:
        return current_app.config['DOCS_BUILD_DIR']
    relengapi_dist = pkg_resources.working_set.find(
        pkg_resources.Requirement.parse('relengapi'))
    return os.path.join(
        pkg_resources.resource_filename(relengapi_dist.as_requirement(), ''),
        'docs_build_dir')


def get_support(quiet=False):
    if not hasattr(current_app, 'docs_websupport'):
        basebuilddir = get_basebuilddir()
        srcdir = os.path.join(basebuilddir, 'src')
        builddir = os.path.join(basebuilddir, 'result')
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


def copy_resources(req, src, dest):
    """
    Copy resources recursively from ``src``, relative to the setuptools
    Requirement ``req``, to the actual filesystem directory ``dest``.
    This uses the resource-access API, and as such is compatible with zip
    distributions.
    """
    src = src.rstrip('/')
    if not pkg_resources.resource_exists(req, src):
        return
    if pkg_resources.resource_isdir(req, src):
        if not os.path.exists(dest):
            os.makedirs(dest)
        for f in pkg_resources.resource_listdir(req, src):
            copy_resources(req, '{0}/{1}'.format(src, f),
                                os.path.join(dest, f))
    else:
        logger.debug("copying %s::%s to %r", req, src, dest)
        shutil.copyfileobj(pkg_resources.resource_stream(req, src),
                           open(dest, "wb"))


def copy_base_doc_tree(destdir):
    req = pkg_resources.Requirement.parse('relengapi')
    req = pkg_resources.working_set.find(req).as_requirement()
    logger.info("Copying base doc tree from %s", req)
    copy_resources(req, 'relengapi/blueprints/docs/base', destdir)


def merge_doc_tree(req, destdir):
    dist = pkg_resources.working_set.find(req)
    if not pkg_resources.resource_isdir(req, 'relengapi/docs'):
        return
    logger.info("Merging doc tree from %s", req)

    # merging works like this:
    #  $dist/relengapi/docs/$tld/ -> $destdir/$tld/$distname/
    # where $tld is a top-level directory (e.g., 'deployment').

    for f in pkg_resources.resource_listdir(req, 'relengapi/docs'):
        srcpath = 'relengapi/docs/{}'.format(f)
        if not pkg_resources.resource_isdir(req, srcpath):
            logger.warning(
                "%s:%r is not a directory; ignored", req, srcpath)
            continue
        if not os.path.isdir(os.path.join(destdir, f)):
            logger.warning("%s:%r does not corespond to a top-level directory "
                           "in the base doc tree; ignored", req, srcpath)
            continue
        # sort relengapi's docs above other projects
        dist_name = dist.key if dist.key != 'relengapi' else '@relengapi'
        destpath = os.path.join(destdir, f, dist_name)
        copy_resources(req, srcpath, destpath)


def build(quiet=False):
    # the build process is two-part: first, copy all of the build trees
    # from all installed blueprints into a single tree under basebuilddir/src,
    # then point the WebSupport instance at that directory and build it.
    basebuilddir = get_basebuilddir()
    srcdir = os.path.join(basebuilddir, 'src')
    if os.path.exists(srcdir):
        shutil.rmtree(srcdir)

    # build the framework
    copy_base_doc_tree(srcdir)

    # now enumerate the other distributions providing relengapi blueprints
    entry_points = pkg_resources.iter_entry_points('relengapi_blueprints')
    dists = sorted(set(ep.dist for ep in entry_points))
    for dist in dists:
        merge_doc_tree(dist.as_requirement(), srcdir)

    # now that the source is accumulated, build it
    get_support(quiet=quiet).build()


class BuildDocsSubcommand(subcommands.Subcommand):

    def make_parser(self, subparsers):
        parser = subparsers.add_parser('build-docs',
                                       help='make a built version of the '
                                            'sphinx documentation')
        parser.add_argument("--debug", action='store_true',
                            help="Show debug logging")
        parser.add_argument("--quiet", action='store_true',
                            help="Quiet output")
        return parser

    def run(self, parser, args):
        if not args.debug:
            logger.setLevel(logging.INFO)
        build(quiet=args.quiet)
