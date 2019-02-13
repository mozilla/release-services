# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import abc
import os
from datetime import datetime
from datetime import timedelta

from cli_common.log import get_logger
from cli_common.phabricator import PhabricatorAPI
from cli_common.taskcluster import TASKCLUSTER_DATE_FORMAT
from static_analysis_bot.config import settings
from static_analysis_bot.report.debug import DebugReporter
from static_analysis_bot.revisions import Revision

logger = get_logger(__name__)

TASKCLUSTER_NAMESPACE = 'project.releng.services.project.{channel}.static_analysis_bot.{name}'
TASKCLUSTER_INDEX_TTL = 7  # in days


class Workflow(abc.ABC):
    '''
    Static analysis workflow
    '''
    def __init__(self, reporters, analyzers, index_service, queue_service, phabricator_api):
        assert isinstance(analyzers, list)
        assert len(analyzers) > 0, \
            'No analyzers specified, will not run.'
        self.analyzers = analyzers
        assert 'MOZCONFIG' in os.environ, \
            'Missing MOZCONFIG in environment'

        # Use share phabricator API client
        assert isinstance(phabricator_api, PhabricatorAPI)
        self.phabricator = phabricator_api

        # Load reporters to use
        self.reporters = reporters
        if not self.reporters:
            logger.warn('No reporters configured, this analysis will not be published')

        # Always add debug reporter and Diff reporter
        self.reporters['debug'] = DebugReporter(output_dir=settings.taskcluster.results_dir)

        # Use TC services client
        self.index_service = index_service
        self.queue_service = queue_service

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        '''
        Main workflow method to implement in subclasses
        '''

    def index(self, revision, **kwargs):
        '''
        Index current task on Taskcluster index
        '''
        assert isinstance(revision, Revision)

        if settings.taskcluster.local or self.index_service is None:
            logger.info('Skipping taskcluster indexing', rev=str(revision), **kwargs)
            return

        # Build payload
        payload = revision.as_dict()
        payload.update(kwargs)

        # Always add the indexing
        now = datetime.utcnow()
        payload['indexed'] = now.strftime(TASKCLUSTER_DATE_FORMAT)

        # Index for all required namespaces
        for name in revision.namespaces:
            namespace = TASKCLUSTER_NAMESPACE.format(channel=settings.app_channel, name=name)
            self.index_service.insertTask(
                namespace,
                {
                    'taskId': settings.taskcluster.task_id,
                    'rank': 0,
                    'data': payload,
                    'expires': (now + timedelta(days=TASKCLUSTER_INDEX_TTL)).strftime(TASKCLUSTER_DATE_FORMAT),
                }
            )
