# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from backend_common import log
import taskcluster


logger = log.get_logger()


def taskcluster_cache(namespace='gecko.v2',
                      decision_task_namespace='latest.firefox.decision',
                      ):
    """ TODO: add description
    """

    logger.info('Querying taskcluster for list of branches in "%s" '
                'namespace.' % namespace)

    # taskcluster api's we need to query
    index = taskcluster.Index()
    queue = taskcluster.Queue()

    branches = dict()
    for branch in index.listNamespaces(namespace, dict(limit=1000))\
                       .get('namespaces', []):

        branch_name = branch.get('name')
        if not branch_name:
            logger.error('Name for branch "%s" not found.' % branch)

        # compose decision_task index fro
        branch_decision_task_name = '%s.%s.%s' % (
            namespace, branch_name, decision_task_namespace)

        # fetch decision task from index service
        try:
            branch_decision_task = index.findTask(branch_decision_task_name)
        except taskcluster.exceptions.TaskclusterRestFailure:
            logger.info(
                'Decision task "%s" not found.' % branch_decision_task_name)
            continue

        branches[branch_name] = dict()

        logger.info('Decision task "%s" found.' % branch_decision_task_name)

        # we try to look for all tasks that were scheduled by this decision
        # task. this is stored as artifict in 'public/task-graph.json' or
        # 'public/graph.json'
        branch_tasks = None
        try:
            graph = queue.getLatestArtifact(
                branch_decision_task['taskId'],
                'public/task-graph.json',
            )
            branch_tasks = list(graph.values())
            logger.debug(
                'Tasks for branch "%s" decision task "%s" found in '
                '"public/task-graph.json" artifact.' % (
                    branch_name,
                    branch_decision_task_name,
                )
            )
        except taskcluster.exceptions.TaskclusterRestFailure:
            try:
                graph = queue.getLatestArtifact(
                    branch_decision_task['taskId'],
                    'public/graph.json',
                )
                branch_tasks = graph.get('tasks', [])
                logger.debug(
                    'Tasks for branch "%s" decision task "%s" found in '
                    '"public/graph.json" artifact.' % (
                        branch_name,
                        branch_decision_task_name,
                    )
                )
            except taskcluster.exceptions.TaskclusterRestFailure:
                logger.error(
                    'Tasks for branch "%s" and its decision task "%s" '
                    'couldn\'t be found.' % (
                        branch_name,
                        branch_decision_task_name,
                    )
                )
                # we don't throw error but continue and report it in logs
                continue

        # loop through all the tasks and collect caches per worker type
        for branch_task in branch_tasks:

            task = branch_task.get('task')
            if not task:
                logger.error(
                    'Task for branch_task "%s" of branch "%s" couldn\'t be '
                    'found.' % (
                        branch_task,
                        branch_name,
                    )
                )
                # we don't throw error but continue and report it in logs
                continue

            provisioner_id = task.get('provisionerId')
            if not provisioner_id:
                logger.error(
                    'provisionerId for task "%s" of branch "%s" couldn\'t be '
                    'found.' % (
                        task,
                        branch_name,
                    )
                )
                # we don't throw error but continue and report it in logs
                continue

            worker_type = task.get('workerType')
            if not worker_type:
                logger.error(
                    'workerType for task "%s" of branch "%s" couldn\'t be '
                    'found.' % (
                        task,
                        branch_name,
                    )
                )
                # we don't throw error but continue and report it in logs
                continue

            task_payload = task.get('payload')
            if not task_payload:
                logger.error(
                    'payload for task "%s" of branch "%s" couldn\'t be '
                    'found.' % (
                        task,
                        branch_name,
                    )
                )
                # we don't throw error but continue and report it in logs
                continue

            task_cache_names = list(task_payload.get('cache', dict()).keys())

            branch_caches_id = '%s/%s' % (provisioner_id, worker_type)
            branch_caches = branches[branch_name].get(branch_caches_id)
            if branch_caches:
                branch_caches['caches'] = list(set(
                    branch_caches['caches'] + task_cache_names
                ))
            else:
                branch_caches = dict(
                    provisioner_id=provisioner_id,
                    workerType=worker_type,
                    caches=task_cache_names,
                )

            branches[branch_name][branch_caches_id] = branch_caches

    return branches
