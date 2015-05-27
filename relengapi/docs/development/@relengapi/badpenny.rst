Periodic Tasks
==============

RelengAPI components that need to execute a task periodically can use *badpenny* to configure this.

Defining a Task
---------------

Tasks are simple Python functions, decorated with :py:func:`relengapi.lib.badpenny.periodic_task` or :py:func:`~relengapi.lib.cron_task`::

    from relengapi.lib import badpenny

    @badpenny.periodic_task(seconds=300)
    def do_this_often(job_status):
        ...

    @badpenny.cron_task('5 * * * *')
    def do_this_hourly(job_status):
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
Like all celery tasks, they execute in a regular Flask application context, so access to the DB is just the same as it would be from a view function.

Each task function gets a :py:class:`JobStatus` instance as an argument, which can be used to report status and progress of the task.

If the task function raises an exception, the traceback is added to the job's logs and it is marked as failed.
Otherwise, the job is considered successful and the return value of the task function is JSON-ified and recorded as the job's result.

JobStatus Objects
.................

.. py:class:: JobStatus

    .. py:method:: log_message(message)

        Add the given message to the logs of the job exeuction.
        Logs are stored as a string in the database, so tasks should be careful to limit the amount of logging they perform.
        A good target is less than 4KB per job.
