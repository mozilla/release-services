# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from flask import Flask
from flask import g
from flask import render_template
from relengapi import celery
from relengapi import db
from relengapi.lib import api
from relengapi.lib import auth
from relengapi.lib import layout
from relengapi.lib import monkeypatches
from relengapi.lib import permissions
import pkg_resources
import relengapi
import logging
import wsme.types

# set up the 'relengapi' namespace; it's a namespaced module, so no code
# is allowed in __init__.py
relengapi.p = permissions.p
relengapi.apimethod = api.apimethod

# apply monkey patches
monkeypatches.monkeypatch()

logger = logging.getLogger(__name__)

_blueprints = None


def get_blueprints():
    # get blueprints from pkg_resources.  We're careful to load all of the
    # blueprints exactly once and before registering any of them, as this
    # ensures everything is imported before any of the @bp.register-decorated
    # methods are called
    global _blueprints
    if not _blueprints:
        entry_points = pkg_resources.iter_entry_points('relengapi_blueprints')
        _blueprints = [(ep.name, ep.load()) for ep in entry_points]
    return _blueprints


class BlueprintInfo(wsme.types.Base):
    "Information about an installed Blueprint"

    #: Python distribution containing this blueprint
    distribution = unicode

    #: Version of the blueprint (really, of its distribution)
    version = unicode


class DistributionInfo(wsme.types.Base):
    "Information about an installed Python distribution"

    #: Name of the distribution
    project_name = unicode

    #: Version of the distribution
    version = unicode


class VersionInfo(wsme.types.Base):
    "Information about installed software versions"

    #: All installed Python distributions, by ``project_name``
    distributions = {unicode: DistributionInfo}

    #: All installed blueprints, by name
    blueprints = {unicode: BlueprintInfo}


def create_app(cmdline=False, test_config=None):
    blueprints = get_blueprints()

    app = Flask(__name__)
    if test_config:
        app.config.update(**test_config)
    else:
        app.config.from_envvar('RELENGAPI_SETTINGS')

    # add the necessary components to the app
    app.db = db.make_db(app)
    app.celery = celery.make_celery(app)
    layout.init_app(app)
    auth.init_app(app)
    api.init_app(app)

    for name, bp in blueprints:
        if cmdline:
            logger.info("registering blueprint %s", name)
        app.register_blueprint(bp, url_prefix='/%s' % name)

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
        bp_widgets = [tpl for (_, tpl, condition) in bp_widgets if not condition or condition()]
        return render_template('root.html', bp_widgets=bp_widgets)

    @app.route('/versions')
    @api.apimethod(VersionInfo)
    def versions():
        dists = {}
        for dist in pkg_resources.WorkingSet():
            dists[dist.key] = DistributionInfo(project_name=dist.project_name,
                                               version=dist.version)
        blueprints = {}
        for ep in pkg_resources.iter_entry_points('relengapi_blueprints'):
            blueprints[ep.name] = BlueprintInfo(distribution=ep.dist.key,
                                                version=ep.dist.version)
        return VersionInfo(distributions=dists, blueprints=blueprints)

    return app
