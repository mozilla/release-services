Periodic Tasks
==============

RelengAPI supports executing tasks periodically: a kind of distributed cron.
Applications within the API use this functionality to perform regular maintenance tasks, prepare reports, and so on.
The component implementing this functionality is named "badpenny".

Configuration
-------------

Badpenny configuration is performed in code, and its configuration cannot be modified from the API.
However, extensive read-only access is provided for administrative purposes, to those with the ``base.badpenny.view`` permission.

Tasks and Jobs
--------------

.. api:autotype:: BadpennyTask

    A badpenny *task* is a named action that occurs on a schedule.
    That schedule is determined by the code implementing the action.

    Tasks are defined in code, so they cannot be modified via the API.
    Tasks that were once defined in the code, but are no longer, are considered "inactive".

.. api:autotype:: BadpennyJob

    A *job* is a single execution of a task's action.
    A job's life-cycle begins when it is *created* from the task.
    The job *starts* when it is actually executed on a machine in the celery cluster.
    The job *completes* when that execution is finished -- successfully or not.

    Each job has a success flag, as well as a JSON-formatted result with arbitrary contents and some log output (:api:type:`BadpennyJobLog`) to help with debugging.


.. api:autotype:: BadpennyJobLog

    This type represents a job log.


Endpoints
---------

.. api:autoendpoint:: badpenny.*
