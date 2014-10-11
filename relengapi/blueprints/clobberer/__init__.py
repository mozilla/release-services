# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask_login
import logging
import time
import os

from sqlalchemy import desc

from flask import Blueprint
from flask import g
from flask import request
from flask import render_template
from flask.ext.login import current_user

from models import Build
from models import ClobberTime
from models import DB_DECLARATIVE_BASE

from rest import ClobberRequest

from relengapi import apimethod

logger = logging.getLogger(__name__)

bp = Blueprint(
    'clobberer',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@bp.record_once
def apply_settings(state):
    "Apply blueprint specific settings to the parent app."
    if state.app.config['SQLALCHEMY_DATABASE_URIS'].get(DB_DECLARATIVE_BASE) is None:
        state.app.config['SQLALCHEMY_DATABASE_URIS'][DB_DECLARATIVE_BASE] = os.environ.get(
            'CLOBBERER_DB_URI',
            'sqlite:////tmp/clobberer.db'
        )


@bp.route('/')
@flask_login.login_required
def root():
    context = {'who': current_user}
    return render_template('clobberer.html', **context)


@bp.route('/clobber', methods=['POST'])
@apimethod(None, body=ClobberRequest)
def clobber(body):
    "Request a clobber."

    session = g.db.session(DB_DECLARATIVE_BASE)
    clobber_time = ClobberTime(
        branch=body.branch,
        slave=body.slave,
        builddir=body.builddir,
        lastclobber=int(time.time()),
        who=unicode(current_user)
    )
    session.add(clobber_time)
    session.commit()
    return None


@bp.route('/lastclobber', methods=['GET'])
def clobbertimes():
    "Get the max/last clobber time for a particular builddir and branch."

    session = g.db.session(DB_DECLARATIVE_BASE)
    now = int(time.time())
    branch = request.args.get('branch')
    slave = request.args.get('slave')
    builddir = request.args.get('builddir')
    buildername = request.args.get('buildername')
    master = request.args.get('master')
    # TODO: Move the builds update to a separate endpoint (requires client changes)
    build = Build.as_unique(
        session,
        branch=branch,
        master=master,
        slave=slave,
        builddir=builddir,
        buildername=buildername,
    )
    build.last_build_time = now
    session.add(build)
    session.commit()

    max_ct = session.query(ClobberTime).filter(
        ClobberTime.builddir == builddir, ClobberTime.branch == branch
    ).order_by(desc(ClobberTime.lastclobber)).first()

    if max_ct:
        return "{}:{}:{}\n".format(max_ct.builddir, max_ct.lastclobber, max_ct.who)
    return ""
