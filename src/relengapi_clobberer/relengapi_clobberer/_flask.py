# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import datetime
import wsme.types

from flask import g

from relengapi_common.api import apimethod
from relengapi_common.permissions import p
from relengapi_clobberer import api
from relengapi_clobberer.models import DB_DECLARATIVE_BASE


__name__ = 'clobberer'


class Branch(wsme.types.Base):
    """Represents branches of buildbot
    """
    name = wsme.types.wsattr(unicode, mandatory=True)
    data = wsme.types.wsattr(
        {unicode: [unicode]}, mandatory=False, default=list())


def init_app(app):

    p.clobberer.post.clobber.doc('Submit clobber requests')

    caches_to_skip = app.config.get('TASKCLUSTER_CACHES_TO_SKIP', [])

    @app.route('/')
    def root():
        # TODO: point to tools page for clobberer or documentation
        return 'Clobberer is running ...'

    @app.route('/buildbot', methods=['GET'])
    @apimethod([Branch])
    def get_buildout():
        """List of all buildbot branches.
        """
        session = g.db.session(DB_DECLARATIVE_BASE)
        # TODO: only cache this in production
        #branches = app.cache.cached()(api.buildbot_branches)(session)
        branches = api.buildbot_branches(session)
        return [
            Branch(
                name=branch['name'],
                data={
                    name: [
                        datetime.datetime.fromtimestamp(
                            builder.lastclobber).strftime("%Y-%m-%d %H:%M:%S")
                        for builder in builders
                        if builder.lastclobber
                    ]
                    for name, builders in branch['builders'].items()
                }
            )
            for branch in branches
        ]
    @app.route('/buildbot', methods=['POST'])
    @apimethod(unicode, body=[(unicode, unicode)])  # TODO: do we need more specific types
    @p.clobberer.post.clobber.require()
    def post_buildout(body):
        """
        Request clobbers for particular branches and builddirs.
        """
        session = g.db.session(DB_DECLARATIVE_BASE)
        for clobber in body:
            _add_clobber(
                app,
                session,
                branch=clobber.branch,
                builddir=clobber.builddir,
                slave=clobber.slave
            )
        session.commit()
        return None


    @app.route('/taskcluster', methods=['GET'])
    @apimethod([Branch])
    def get_taskcluster():
        """List of all the gecko branches with their worker types
        """
        branches = app.cache.cached()(api.taskcluster_branches)()
        return [
            Branch(
                name=branchName,
                data={
                    workerName: filter(lambda x: x not in caches_to_skip, worker['caches'])  # noqa
                    for workerName, worker in branch['workerTypes'].items()
                }
            )
            for branchName, branch in branches.items()
        ]

    # TODO post_taskcluster

    return api

    # @app.route('/buildbot/clobber/by-builder', methods=['POST'])
    # @apimethod(None, body=[rest.ClobberRequestByBuilder])
    # @p.clobberer.post.clobber.require()
    # def clobber_by_builder(body):
    #     """
    #     Request clobbers for app builddirs associated with a particular
    #     buildername.
    #     """
    #     session = g.db.session(DB_DECLARATIVE_BASE)
    #     for clobber in body:
    #         builddirs_query = session\
    #             .query(Build.builddir, Build.branch)\
    #             .filter(Build.buildername == clobber.buildername)
    #         if clobber.branch is not None:
    #             builddirs_query = \
    #                 builddirs_query.filter(Build.branch == clobber.branch)

    #         for result in builddirs_query.distinct():
    #             _add_clobber(
    #                 app,
    #                 session,
    #                 builddir=result[0],
    #                 branch=result[1],
    #                 slave=clobber.slave
    #             )
    #     session.commit()
    #     return None

    # @app.route('/lastclobber/branch/by-builder/<string:branch>',
    #            methods=['GET'])
    # @apimethod({unicode: [rest.ClobberTime]}, unicode)
    # def lastclobber_by_builder(branch):
    #     """Return a dictionary of most recent ClobberTimes grouped by
    #        buildername.
    #     """
    #     session = g.db.session(DB_DECLARATIVE_BASE)

    #     # Isolates the maximum lastclobber for each builddir on a branch
    #     max_ct_sub_query = session.query(
    #         func.max(ClobberTime.lastclobber).label('lastclobber'),
    #         ClobberTime.builddir,
    #         ClobberTime.branch
    #     ).group_by(
    #         ClobberTime.builddir,
    #         ClobberTime.branch
    #     ).filter(ClobberTime.branch == branch).subquery()

    #     # Finds the "greatest n per group" by joining with the
    #     # max_ct_sub_query
    #     # This is necessary to get the correct "who" values
    #     sub_query = session.query(ClobberTime).join(max_ct_sub_query, and_(
    #         ClobberTime.builddir == max_ct_sub_query.c.builddir,
    #         ClobberTime.lastclobber == max_ct_sub_query.c.lastclobber,
    #         ClobberTime.branch == max_ct_sub_query.c.branch)).subquery()

    #     # Attaches builddirs, along with their max lastclobber to a
    #     # buildername
    #     full_query = session.query(
    #         Build.buildername,
    #         Build.builddir,
    #         sub_query.c.lastclobber,
    #         sub_query.c.who
    #     ).outerjoin(
    #         sub_query,
    #         Build.builddir == sub_query.c.builddir,
    #     ).filter(
    #         Build.branch == branch,
    #         not_(Build.buildername.startswith(BUILDER_REL_PREFIX))
    #     ).distinct().order_by(Build.buildername)

    #     summary = collections.defaultdict(list)
    #     for result in full_query:
    #         buildername, builddir, lastclobber, who = result
    #         summary[buildername].append(
    #             rest.ClobberTime(
    #                 branch=branch,
    #                 builddir=builddir,
    #                 lastclobber=lastclobber,
    #                 who=who
    #             )
    #         )
    #     return summary

    # @app.route('/lastclobber', methods=['GET'])
    # def lastclobber():
    #     "Get the max/last clobber time for a particular builddir and branch."

    #     session = g.db.session(DB_DECLARATIVE_BASE)
    #     now = int(time.time())
    #     branch = request.args.get('branch')
    #     slave = request.args.get('slave')
    #     builddir = request.args.get('builddir')
    #     buildername = request.args.get('buildername')
    #     # TODO: Move the builds update to a separate endpoint (requires
    #     # client changes)
    #     build = Build.as_unique(
    #         session,
    #         branch=branch,
    #         builddir=builddir,
    #         buildername=buildername,
    #     )
    #     # Always force the time to update
    #     build.last_build_time = now
    #     session.add(build)
    #     session.commit()

    #     max_ct = session.query(ClobberTime).filter(
    #         ClobberTime.builddir == builddir,
    #         ClobberTime.branch == branch,
    #         # a NULL slave value signifies all slaves
    #         or_(ClobberTime.slave == slave, ClobberTime.slave == None)  # noqa
    #     ).order_by(desc(ClobberTime.lastclobber)).first()

    #     if max_ct:
    #         # The client parses this result by colon as:
    #         # builddir, lastclobber, who = urlib2.open.split(':')
    #         # as such it's important for this to be plain text and have
    #         # no extra colons within the field values themselves
    #         return "{}:{}:{}\n".format(
    #             max_ct.builddir, max_ct.lastclobber, max_ct.who)
    #     return ""

    # @app.route('/forceclobber', methods=['GET'])
    # def forceclobber():
    #     """
    #     Coerce the client to clobber by always returning a future clobber
    #     time. This works because the client decides to clobber based on a
    #     timestamp comparison.
    #     """
    #     future_time = int(time.time()) + 3600
    #     builddir = request.args.get('builddir')
    #     return "{}:{}:forceclobber".format(builddir, future_time)

    # @app.route('/taskcluster/clobber', methods=['POST'])
    # @apimethod(None, body=[rest.TCPurgeCacheRequest])
    # @p.clobberer.post.clobber.require()
    # def taskcluster_purgecache(body):
    #     """Purge cache on taskcluster
    #     """

    #     credentials = []

    #     # TODO: check that these 2 are set in init_app
    #     client_id = current_app.config.get('TASKCLUSTER_CLIENT_ID')
    #     access_token = current_app.config.get('TASKCLUSTER_ACCESS_TOKEN')

    #     if client_id and access_token:
    #         credentials = [dict(
    #             credentials=dict(
    #                 clientId=client_id,
    #                 accessToken=access_token,
    #             ))]

    #     purge_cache = taskcluster.PurgeCache(*credentials)

    #     for item in body:
    #         purge_cache.purgeCache(item.provisionerId,
    #                                item.workerType,
    #                                dict(cacheName=item.cacheName))

    #     return None

# def _add_clobber(app, session, branch, builddir, slave=None):
#     """
#     A common method for adding clobber times to a session. The session passed
#     in is returned; but is only committed if the commit option is True.
#     """
#     if re.search('^' + BUILDDIR_REL_PREFIX + '.*', builddir) is None:
#         try:
#             who = current_user.authenticated_email
#         except AttributeError:
#             if current_user.anonymous:
#                 who = 'anonymous'
#             else:
#                 # TokenUser doesn't show up as anonymous; but also has no
#                 # authenticated_email
#                 who = 'automation'
#
#         clobber_time = ClobberTime.as_unique(
#             session,
#             branch=branch,
#             builddir=builddir,
#             slave=slave,
#         )
#         clobber_time.lastclobber = int(time.time())
#         clobber_time.who = who
#         session.add(clobber_time)
#         return None
#     app.log.debug('Rejecting clobber of builddir with release '
#                   'prefix: {}'.format(builddir))
#     return None
