# -*- coding: utf-8 -*-
import os
from threading import Lock
import time

from cli_common.log import get_logger

from shipit_code_coverage import taskcluster
from shipit_code_coverage.utils import mkdir, ThreadPoolExecutorResult


logger = get_logger(__name__)


FINISHED_STATUSES = ['completed', 'failed', 'exception']
ALL_STATUSES = FINISHED_STATUSES + ['unscheduled', 'pending', 'running']
STATUS_VALUE = {
    'exception': 1,
    'failed': 2,
    'completed': 3,
}


class ArtifactsHandler(object):

    def __init__(self, task_ids, suites_to_ignore):
        self.task_ids = task_ids
        self.suites_to_ignore = suites_to_ignore
        self.download_tasks = {}
        self.download_tasks_lock = Lock()

    def generate_path(self, platform, chunk, artifact):
        return 'ccov-artifacts/%s_%s_%s' % (platform, chunk, os.path.basename(artifact['name']))

    def get_chunks(self):
        return list(set([f.split('_')[1] for f in os.listdir('ccov-artifacts')]))

    def get(self, platform=None, suite=None, chunk=None):
        files = os.listdir('ccov-artifacts')

        if suite is not None and chunk is not None:
            raise Exception('suite and chunk can\'t both have a value')

        # Filter artifacts according to platform, suite and chunk.
        filtered_files = []
        for fname in files:
            if platform is not None and not fname.startswith('%s_' % platform):
                continue

            if suite is not None and suite not in fname:
                continue

            if chunk is not None and ('%s_code-coverage' % chunk) not in fname:
                continue

            filtered_files.append('ccov-artifacts/' + fname)

        return filtered_files

    def should_download(self, status, chunk_name, platform_name):
        with self.download_tasks_lock:
            # If the chunk hasn't been downloaded before, this is obviously the best task
            # to download it from.
            if (chunk_name, platform_name) not in self.download_tasks:
                download_lock = Lock()
                self.download_tasks[(chunk_name, platform_name)] = {
                    'status': status,
                    'lock': download_lock,
                }
            else:
                task = self.download_tasks[(chunk_name, platform_name)]

                if STATUS_VALUE[status] > STATUS_VALUE[task['status']]:
                    task['status'] = status
                    download_lock = task['lock']
                else:
                    return None

            download_lock.acquire()
            return download_lock

    def download(self, test_task):
        status = test_task['status']['state']
        assert status in ALL_STATUSES
        while status not in FINISHED_STATUSES:
            time.sleep(60)
            status = taskcluster.get_task_status(test_task['status']['taskId'])['status']['state']
            assert status in ALL_STATUSES

        chunk_name = taskcluster.get_chunk(test_task['task']['metadata']['name'])
        platform_name = taskcluster.get_platform(test_task['task']['metadata']['name'])
        # Ignore awsy and talos as they aren't actually suites of tests.
        if any(to_ignore in chunk_name for to_ignore in self.suites_to_ignore):
            return

        # If we have already downloaded this chunk from another task, check if the
        # other task has a better status than this one.
        download_lock = self.should_download(status, chunk_name, platform_name)
        if download_lock is None:
            return

        test_task_id = test_task['status']['taskId']
        for artifact in taskcluster.get_task_artifacts(test_task_id):
            if not any(n in artifact['name'] for n in ['code-coverage-grcov.zip', 'code-coverage-jsvm.zip']):
                continue

            artifact_path = self.generate_path(platform_name, chunk_name, artifact)
            taskcluster.download_artifact(artifact_path, test_task_id, artifact['name'])
            logger.info('%s artifact downloaded' % artifact_path)

        download_lock.release()

    def download_all(self):
        mkdir('ccov-artifacts')

        # The test tasks for the Linux and Windows builds are in the same group,
        # but the following code is generic and supports build tasks split in
        # separate groups.
        groups = set([taskcluster.get_task_details(build_task_id)['taskGroupId'] for build_task_id in self.task_ids.values()])
        test_tasks = [
            task
            for group in groups
            for task in taskcluster.get_tasks_in_group(group)
            if taskcluster.is_coverage_task(task)
        ]

        def download_task(test_task):
            return lambda: self.download(test_task)

        with ThreadPoolExecutorResult() as executor:
            for test_task in test_tasks:
                executor.submit(download_task(test_task))

        logger.info('Code coverage artifacts downloaded')
