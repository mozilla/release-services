Periodic Tasks
==============

Periodic tasks are configured in the source code, triggered via a run of ``relengapi badpenny-cron`` (usually in a crontask), and finally executed on the Celery cluster.
The difficult bit of running periodic tasks in a distributed application is starting one and only one job for a task at the desired time.
RelengAPI's approach is for the deployment to ensure that only one ``relengapi badpenny-cron`` runs at any time, eliminating the possibility of a race condition.
This script runs very quickly, just querying the database and queueing new jobs -- it does not actually perform any work.

The key to configuring this reliably is to run the crontask periodically on several servers, with offset times.
For example, if you require per-minute resolution with two servers, run the crontask on one server at even minutes and on the other server at odd minutes.

Celery
------

Periodic tasks actually *execute* in the celery cluster, so be sure you've set that up.

Crontask
--------

A single-host crontask might look like this:

.. code-block: none
    * * * * * * RELENGAPI_SETTINGS=/path/to/settings.py /path/to/relengapi --quiet badpenny-cron

The ``--quiet`` silences "normal" output, leaving only warning-level and higher logging to stdout.

Cleanup
-------

Every job is logged in the database, and for a busy production environment this can become a lot of data!

A cleanup task runs regularly, purging information about old jobs.
The ``BADPENNY_OLD_JOB_DAYS`` configuration parameter specifies the number of days after which jobs will be purged from the database, defaulting to 7.
