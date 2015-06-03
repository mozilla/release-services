# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import pkg_resources
import relengapi
import wsme.types

from flask import Flask
from flask import g
from flask import render_template
from relengapi.lib import api
from relengapi.lib import auth
from relengapi.lib import aws
from relengapi.lib import celery
from relengapi.lib import db
from relengapi.lib import introspection
from relengapi.lib import layout
from relengapi.lib import memcached
from relengapi.lib import monkeypatches
from relengapi.lib import permissions

# set up the 'relengapi' namespace; it's a namespaced module, so no code
# is allowed in __init__.py
relengapi.p = permissions.p
relengapi.apimethod = api.apimethod

# apply monkey patches
monkeypatches.monkeypatch()

logger = logging.getLogger(__name__)


class BlueprintInfo(wsme.types.Base):

    "Information about an installed Blueprint"

    #: Python distribution containing this blueprint (always 'relengapi')
    distribution = unicode

    #: Version of the blueprint (really, of its distribution)
    version = unicode


class DistributionInfo(wsme.types.Base):

    "Information about an installed Python distribution"

    #: Name of the distribution
    project_name = unicode

    #: Version of the distribution
    version = unicode

    #: Additional RelengAPI-specific metadata (deprecated; always empty)
    relengapi_metadata = {unicode: unicode}


class VersionInfo(wsme.types.Base):

    "Information about installed software versions"

    #: All installed Python distributions, by ``project_name``
    distributions = {unicode: DistributionInfo}

    #: All installed blueprints, by name
    blueprints = {unicode: BlueprintInfo}


def _load_bp(n):
    relengapi_mod = __import__('relengapi.blueprints.' + n)
    return getattr(relengapi_mod.blueprints, n).bp

blueprints = [_load_bp(n) for n in [
    'auth',
    'badpenny',
    'base',
    'clobberer',
    'docs',
    'mapper',
    'slaveloan',
    'tokenauth',
    'tooltool',
]]


def create_app(cmdline=False, test_config=None):
    app = Flask(__name__)
    env_var = 'RELENGAPI_SETTINGS'
    if test_config:
        app.config.update(**test_config)
    else:
        if env_var in os.environ and os.environ[env_var]:
            app.config.from_envvar(env_var)
        else:
            logger.warning("Using default settings; to configure relengapi, set "
                           "%s to point to your settings file" % env_var)

    # add the necessary components to the app
    app.db = db.make_db(app)
    app.celery = celery.make_celery(app)
    layout.init_app(app)
    auth.init_app(app)
    api.init_app(app)
    aws.init_app(app)
    memcached.init_app(app)

    app.relengapi_blueprints = {}
    for bp in blueprints:
        if cmdline:
            logger.info("registering blueprint %s", bp.name)
        app.register_blueprint(bp, url_prefix='/%s' % bp.name)
        app.relengapi_blueprints[bp.name] = bp

    # set up a random session key if none is specified
    if not app.config.get('SECRET_KEY'):
        logger.warning("setting per-process session key - sessions will be reset on "
                       "process restart")
        app.secret_key = os.urandom(24)

    @app.before_request
    def add_db():
        g.db = app.db

    @app.route('/')
    def root():
        # render all of the blueprints' templates first
        bp_widgets = []
        for bp in app.blueprints.itervalues():
            bp_widgets.extend(bp.root_widget_templates or [])
        bp_widgets.sort()
        bp_widgets = [
            tpl for (_, tpl, condition) in bp_widgets if not condition or condition()]
        return render_template('root.html', bp_widgets=bp_widgets)

    @app.route('/versions')
    @api.apimethod(VersionInfo)
    def versions():
        dists = {}
        for dist in introspection.get_distributions().itervalues():
            dists[dist.key] = DistributionInfo(
                project_name=dist.project_name,
                version=dist.version,
                relengapi_metadata={})
        blueprints = {}
        relengapi_dist = pkg_resources.get_distribution('relengapi')
        for bp in app.relengapi_blueprints.itervalues():
            blueprints[bp.name] = BlueprintInfo(distribution='relengapi',
                                                version=relengapi_dist.version)
        return VersionInfo(distributions=dists, blueprints=blueprints)

    return app
