# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import wsme.types


class BadpennyJob(wsme.types.Base):

    """A job is a single occurrence of a task."""

    #: unique job id
    id = wsme.types.wsattr(int, mandatory=True)

    #: name of the task that created this job
    task_name = wsme.types.wsattr(unicode, mandatory=True)

    #: time at which this job was created
    created_at = wsme.types.wsattr(datetime.datetime, mandatory=True)

    #: time at which this job started executing
    started_at = wsme.types.wsattr(datetime.datetime, mandatory=False)

    #: time at which this job finished executing
    completed_at = wsme.types.wsattr(datetime.datetime, mandatory=False)

    #: true if the job was successful
    successful = wsme.types.wsattr(bool, mandatory=False)


class BadpennyJobLog(wsme.types.Base):

    #: text log from the job
    content = wsme.types.wsattr(unicode, mandatory=False)


class BadpennyTask(wsme.types.Base):

    """A task describes an operation that occurs periodically."""

    _name = "BadpennyTask"

    #: unique task name (based on the qualified Python function name)
    name = wsme.types.wsattr(unicode, mandatory=True)

    #: last success of the task: -1 (never run), 0 (failed), or 1 (succeeded)
    last_success = wsme.types.wsattr(int, mandatory=True)

    #: all recent jobs for this task; this is only returned when a single task
    # is requested.
    jobs = wsme.types.wsattr([BadpennyJob], mandatory=False)

    #: true if the task is active (that is, if it is defined in the code).
    active = wsme.types.wsattr(bool, mandatory=True)

    #: a pretty description of the task's schedule, if active
    schedule = wsme.types.wsattr(unicode, mandatory=False)
