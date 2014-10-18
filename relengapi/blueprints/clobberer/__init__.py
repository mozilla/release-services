# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import flask_login
import logging
import time

from datetime import datetime
from sqlalchemy import desc
from sqlalchemy import func
from collections import OrderedDict

from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
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


@bp.route('/')
@flask_login.login_required
def root():
    session = g.db.session(DB_DECLARATIVE_BASE)
    context = {'branches': session.query(Build.branch).distinct()}
    return render_template('clobberer.html', **context)


@bp.route('/<string:branch>')
@flask_login.login_required
def clobberer_branch(branch):
    "Page where users select particular builds to clobber (within a branch)."

    session = g.db.session(DB_DECLARATIVE_BASE)

    # Isolates the maximum lastclobber for each builddir on a branch
    sub_query = session.query(
        func.max(ClobberTime.lastclobber).label('lastclobber'),
        ClobberTime.builddir,
        ClobberTime.who
    ).group_by(
        ClobberTime.builddir,
        ClobberTime.branch
    ).filter(ClobberTime.branch == branch).subquery()
    # Attaches builddirs, along with their max lastclobber to a buildername
    builds_query = session.query(
        Build.buildername,
        Build.builddir,
        sub_query.c.lastclobber,
        sub_query.c.who
    ).outerjoin(
        sub_query, Build.builddir == sub_query.c.builddir
    ).filter(Build.branch == branch).order_by(Build.buildername)

    builds = OrderedDict()
    # The idea is to compress builddirs under their matching buildername
    # doing these operations here, rather than in template logic, is preferred
    for result in builds_query:
        buildername, builddir, lastclobber, who = result
        lastclobber_processed = ''
        if lastclobber is not None:
            lastclobber_processed = '{} by {}'.format(
                datetime.fromtimestamp(lastclobber).strftime('%m-%d-%Y %H:%M:%S'),
                who,
            )
        if builds.get(buildername) is None:
            builds[buildername] = {
                'builddir': builddir,
                'lastclobber': lastclobber_processed,
            }
        else:
            # Just split apart duplicate directories by :
            builds[buildername]['builddir'] += ':{}'.format(builddir)

    context = {'branch': branch, 'builds': builds}

    return render_template('clobberer_branch.html', **context)


@bp.route('/clobber', methods=['POST'])
@apimethod(None, body=ClobberRequest)
def clobber(body):
    "Request clobbers for particular builddirs of a branch."

    session = g.db.session(DB_DECLARATIVE_BASE)
    for builddir in body.builddirs:
        clobber_time = ClobberTime(
            branch=body.branch,
            builddir=builddir,
            lastclobber=int(time.time()),
            # Colons break the client's logic
            who=unicode(current_user).strip(':')
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
    # Always force the time to update
    build.last_build_time = now
    session.add(build)
    session.commit()

    max_ct = session.query(ClobberTime).filter(
        ClobberTime.builddir == builddir, ClobberTime.branch == branch
    ).order_by(desc(ClobberTime.lastclobber)).first()

    if max_ct:
        # The client parses this result by colon as:
        # builddir, lastclobber, who = urlib2.open.split(':')
        # as such it's important for this to be plain text and have
        # no extra colons within the field values themselves
        return "{}:{}:{}\n".format(max_ct.builddir, max_ct.lastclobber, max_ct.who)
    return ""


@bp.route('/forceclobber', methods=['GET'])
def forceclobber():
    """
    Coerce the client to clobber by always returning a future clobber time.
    This works because the client decides to clobber based on a timestamp
    comparrison.
    """
    future_time = int(time.time()) + 3600
    builddir = request.args.get('builddir')
    return "{}:{}:forceclobber".format(builddir, future_time)
