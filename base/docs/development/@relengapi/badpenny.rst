Periodic Tasks
==============

RelengAPI components that need to execute a task periodically can use *badpenny* to configure this.

Defining a Task
---------------

Tasks are simple Python functions, decorated with :py:func:`relengapi.lib.badpenny.periodic_task` or :py:func:`~relengapi.lib.cron_task`::

    from relengapi.lib import badpenny

    @badpenny.periodic_task(seconds=300)
    def do_this_often(job):
        ...

    @badpenny.cron_task('5 * * * *')
    def do_this_hourly(job):
        ...

.. py:module:: relengapi.lib.badpenny

.. py:function:: periodic_task(seconds)

    :param integer seconds: seconds between invocations of this task

    Decorate a task function that should be run at regular intervals.

.. py:function:: cron_task(cron_spec)

    :param string cron_spec: cron-like specification of the task schedule

    Decorate a task function that should be run on a cron-like schedule

    The cron specification is handled by `Croniter <https://github.com/taichino/croniter>`_; see its documentation for format details.

Note that the time resolution for tasks is limited by the frequency at which ``relengapi badpenny`` is run, and the capacity of the Celery cluster.


Task Execution
--------------

Tasks are executed in :doc:`Celery Tasks <tasks>` on the celery cluster.
