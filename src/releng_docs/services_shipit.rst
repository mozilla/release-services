Ship-it v2 (aka the "perfect" version)
======================================

Ship-it v2 represents the whole release pipeline, including manual or automated actions.

What is a pipeline ?
--------------------

As of today, a pipeline is a linear sequence of (taskcluster's) tasks groups. In this documentation, a task group will be referenced as a pipeline step.


What is a pipeline step?
------------------------

A pipeline step is a set of tasks which may be represented as taskcluster's tasks groups. A pipeline step depends only on zero or one upstream step. Tasks in a pipeline step may be parallel or sequential. The pipeline doesn't manage tasks in pipeline steps. It just creates them and wait until every task is completed. A pipeline step has to provide some APIs, so the pipeline can know if it's running or completed. When every task is completed, a pipeline step is considered completed and the pipeline proceeds to the next step.


How is this different from taskcluster (and more precisely its queue and worker interaction)?
----------------------------------------------------------------------

Pipelines are meant to overcome the maximum expiration period (which is 5 days) after a taskcluster's task is created. More precisely, releng has to split the release task graph into 2 groups, so the last tasks don't expire before they are actually run. Pipelines automates on the creation of these 2 groups and allows creations of smaller chunks. Thanks to smaller chunks, we represent  human signoffs via 5-day-long-taskcluster-tasks.

Moreover, taskcluster doesn't allow to make a task group depend upon another. Pipelines allow to model releases this way.


DAG vs linear pipeline?
-----------------------

Like said above, pipelines are linear. Releng has decided to model steps via this simple structure in order to not reimplement most of the taskcluster-queue's logic. In other words, taskcluster-queue handles parallelization of tasks, whereas pipeline is a sequence of checkpoints.
