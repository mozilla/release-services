# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import flask_login
import logging
import time

import rest

from sqlalchemy import desc
from sqlalchemy import func

from flask import Blueprint
from flask import url_for
from flask import g
from flask import request
from flask.ext.login import current_user

from models import Build
from models import ClobberTime
from models import DB_DECLARATIVE_BASE

from relengapi.lib import angular
from relengapi.lib import api
from relengapi import apimethod

logger = logging.getLogger(__name__)

bp = Blueprint(
    'clobberer',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@bp.route('/')
@bp.route('/<string:branch>')
@flask_login.login_required
def root(branch=None):
    return angular.template(
        'clobberer.html',
        url_for('.static', filename='clobberer.js'),
        url_for('.static', filename='clobberer.css'),
        lastclobber_by_builder_url=url_for('clobberer.lastclobber_by_builder', branch=''),
        clobber_url=url_for('clobberer.clobber'),
        branches=api.get_data(branches),
        selected_branch=branch
    )


@bp.route('/clobber', methods=['POST'])
@apimethod(None, body=[rest.ClobberRequest])
def clobber(body):
    "Request clobbers for particular branches and builddirs."

    session = g.db.session(DB_DECLARATIVE_BASE)
    for clobber in body:
        clobber_time = ClobberTime(
            branch=clobber.branch,
            builddir=clobber.builddir,
            lastclobber=int(time.time()),
            # Colons break the client's logic
            who=unicode(current_user).strip(':')
        )
        session.add(clobber_time)
    session.commit()
    return None


@bp.route('/branches')
@apimethod([unicode])
def branches():
    "Return a list of all the branches clobberer knows about."
    session = g.db.session(DB_DECLARATIVE_BASE)
    branches = session.query(Build.branch).distinct()
    return [branch[0] for branch in branches]


@bp.route('/lastclobber/branch/by-builder/<string:branch>', methods=['GET'])
@apimethod({unicode: [rest.ClobberTime]}, unicode)
def lastclobber_by_builder(branch):
    "Return a dictionary of most recent ClobberTimes grouped by buildername."

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
    full_query = session.query(
        Build.buildername,
        Build.builddir,
        sub_query.c.lastclobber,
        sub_query.c.who
    ).outerjoin(
        sub_query,
        Build.builddir == sub_query.c.builddir,
    ).filter(Build.branch == branch).distinct().order_by(Build.buildername)

    summary = collections.defaultdict(list)
    for result in full_query:
        buildername, builddir, lastclobber, who = result
        summary[buildername].append(
            rest.ClobberTime(
                branch=branch,
                builddir=builddir,
                lastclobber=lastclobber,
                who=who
            )
        )
    return summary


# Clobberer compatability endpoints. These are drop in replacements for the
# deprecated clobberer service. As such, these endpoints should be deprecated
# as well.


@bp.route('/lastclobber', methods=['GET'])
def lastclobber():
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
