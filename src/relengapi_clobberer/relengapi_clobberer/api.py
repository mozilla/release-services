# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import taskcluster

from sqlalchemy import not_

from relengapi_clobberer.models import ClobbererBuilds


BUILDBOT_BUILDDIR_REL_PREFIX = 'rel-'
BUILDBOT_BUILDER_REL_PREFIX = 'release-'
TASKCLUSTER_DECISION_NAMESPACE = 'gecko.v2.%s.latest.firefox.decision'


def buildout_branches(session):
    """List of all buildbot branches.
    """

    branches = session.query(ClobbererBuilds.branch).distinct()

    # Users shouldn't see any branch associated with a release builddir
    branches = branches.filter(not_(
        ClobbererBuilds.builddir.startswith(BUILDBOT_BUILDDIR_REL_PREFIX)))

    branches = branches.order_by(ClobbererBuilds.branch)

    return branches


def taskcluster_branches():
    """Dict of workerTypes per branch with their respected hashes
    """
    index = taskcluster.Index()
    queue = taskcluster.Queue()

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
        except taskcluster.exceptions.TaskclusterRestFailure:
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
