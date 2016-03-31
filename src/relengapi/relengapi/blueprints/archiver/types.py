# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import wsme.types


class MozharnessArchiveTask(wsme.types.Base):
    """Represents a running task and its current state
    """

    #: this is the current state of the task
    #: e.g. "PENDING", "PROGRESS", "SUCCESS", "FAILURE"
    state = unicode

    #: current msg status of task
    #: e.g. "Downloading archive from hg.m.o"
    status = unicode

    #: archive url origin that s3 item is based off of
    src_url = unicode

    #: s3 links for the archives by region
    s3_urls = {str: str}
