# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import


import sqlalchemy as sa
import taskcluster as tc
import time

from relengapi_common.db import db


BUILDBOT_BUILDDIR_REL_PREFIX = 'rel-'
BUILDBOT_BUILDER_REL_PREFIX = 'release-'
TASKCLUSTER_DECISION_NAMESPACE = 'gecko.v2.%s.latest.firefox.decision'


class Build(db.Model):
    """
    A clobberable builds.
    """

    __tablename__ = 'clobberer_builds'

    id = sa.Column(sa.Integer, primary_key=True)
    branch = sa.Column(sa.String(50), index=True)
    builddir = sa.Column(sa.String(100), index=True)
    buildername = sa.Column(sa.String(100))
    last_build_time = sa.Column(
        sa.Integer,
        nullable=False,
        default=lambda: int(time.time())
    )

    @classmethod
    def unique_hash(cls, branch, builddir, buildername, *args, **kwargs):
        return "{}:{}:{}".format(branch, builddir, buildername)

    @classmethod
    def unique_filter(cls, query, branch, builddir, buildername,
                      *args, **kwargs):
        return query.filter(
            cls.branch == branch,
            cls.builddir == builddir,
            cls.buildername == buildername
        )


class ClobberTime(db.Model):

    __tablename__ = 'clobberer_times'
    __table_args__ = (
        # Index to speed up lastclobber lookups
        sa.Index('ix_get_clobberer_times', 'slave', 'builddir', 'branch'),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    branch = sa.Column(sa.String(50), index=True)
    slave = sa.Column(sa.String(30), index=True)
    builddir = sa.Column(sa.String(100), index=True)
    lastclobber = sa.Column(
        sa.Integer,
        nullable=False,
        default=int(time.time()),
        index=True
    )
    who = sa.Column(sa.String(50))

    @classmethod
    def unique_hash(cls, branch, slave, builddir, *args, **kwargs):
        return "{}:{}:{}".format(branch, slave, builddir)

    @classmethod
    def unique_filter(cls, query, branch, slave, builddir, *args, **kwargs):
        return query.filter(
            cls.branch == branch,
            cls.slave == slave,
            cls.builddir == builddir,
        )


def buildbot_branches(db_session):
    """List of all buildbot branches.
    """

    branches = db_session.query(
        Build.branch
    ).filter(
        # Users shouldn't see any branch associated with a release builddir
        sa.not_(
            Build.builddir.startswith(BUILDBOT_BUILDDIR_REL_PREFIX),
        )
    ).order_by(
        Build.branch
    ).distinct()


    return [
        dict(
            name=branch[0] or "",
            builders=[
                dict(
                    name=builder[0] or "",
                    branch=builder[1] or "",
                    slave=builder[2] or "",
                    builddir=builder[3] or "",
                    lastclobber=builder[4] or -1,
                    who=builder[5] or "",
                )
                for builder in buildbot_branch_builders(db_session, branch[0])
                if all([builder[1], builder[2], builder[3]])
            ],
        )
        for branch in branches
    ]


def buildbot_branch_builders(db_session, branch):
    """Return a dictionary of most recent ClobberTime grouped by
       buildername.
    """
    # Isolates the maximum lastclobber for each builddir on a branch
    max_ct_sub_query = db_session.query(
        sa.func.max(ClobberTime.lastclobber).label('lastclobber'),
        ClobberTime.branch,
        ClobberTime.builddir,
    ).group_by(
        ClobberTime.branch,
        ClobberTime.builddir,
    ).filter(
        ClobberTime.branch == branch
    ).subquery()

    # Finds the "greatest n per group" by joining with the
    # max_ct_sub_query
    # This is necessary to get the correct "who" values
    sub_query = db_session.query(
        ClobberTime
    ).join(
        max_ct_sub_query,
        sa.and_(
            ClobberTime.builddir == max_ct_sub_query.c.builddir,
            ClobberTime.lastclobber == max_ct_sub_query.c.lastclobber,
            ClobberTime.branch == max_ct_sub_query.c.branch,
        ),
    ).subquery()

    # Attaches builddir, along with their max lastclobber to a
    # buildername
    return db_session.query(
        Build.buildername,
        sub_query.c.branch,
        sub_query.c.slave,
        sub_query.c.builddir,
        sub_query.c.lastclobber,
        sub_query.c.who
    ).outerjoin(
        sub_query,
        Build.builddir == sub_query.c.builddir,
    ).filter(
        Build.branch == branch,
        sa.not_(Build.buildername.startswith(BUILDBOT_BUILDER_REL_PREFIX))
    ).order_by(
        Build.buildername
    ).distinct()


## TODO: this will change with tc authentication, it should be passed
#try:
#    who = current_user.authenticated_email
#except AttributeError:
#    if current_user.anonymous:
#        who = 'anonymous'
#    else:
#        # TokenUser doesn't show up as anonymous; but also has no
#        # authenticated_email
#        who = 'automation'

def buildbot_clobber(db_session, branch, slave, builddir, who, log=None):
    """ TODO:
    """

    builder = ClobberTime.unique_hash(branch, slave, builddir)

    match = re.search('^' + BUILDBOT_BUILDDIR_REL_PREFIX + '.*', builddir)
    if match is None:

        if log:
            log.debug('Clobbering builder: {}'.format(builder))

        clobberer_time = ClobberTime.as_unique(
            db_session,
            branch=branch,
            slave=slave,
            builddir=builddir,
        )
        clobberer_time.lastclobber = int(time.time())
        clobberer_time.who = who

        db_session.add(clobberer_time)
        db_session.commit()

        if log:
            log.debug('Clobbered builder: {}'.format(builder))

        return clobberer_time


    if log:
        log.debug('Skipping clobbering of builder: {}'.format(builder))


def taskcluster_branches():
    """Dict of workerTypes per branch with their respected workerTypes
    """
    index = tc.Index()
    queue = tc.Queue()

    result = index.listNamespaces('gecko.v2', dict(limit=1000))

    branches = {
        i['name']: dict(name=i['name'], workerTypes=dict())
        for i in result.get('namespaces', [])
    }

    for branchName, branch in branches.items():

        # decision task might not exist
        try:
            decision_task = index.findTask(
                TASKCLUSTER_DECISION_NAMESPACE % branchName)
            decision_graph = queue.getLatestArtifact(
                decision_task['taskId'], 'public/graph.json')
        except tc.exceptions.TaskclusterRestFailure:
            continue

        for task in decision_graph.get('tasks', []):
            task = task['task']
            task_cache = task.get('payload', dict()).get('cache', dict())

            provisionerId = task.get('provisionerId')
            if provisionerId:
                branch['provisionerId'] = provisionerId

            workerType = task.get('workerType')
            if workerType:
                branch['workerTypes'].setdefault(
                    workerType, dict(name=workerType, caches=[]))

                if len(task_cache) > 0:
                    branch['workerTypes'][workerType]['caches'] = list(set(
                        branch['workerTypes'][workerType]['caches'] +
                        task_cache.keys()
                    ))

    return branches
