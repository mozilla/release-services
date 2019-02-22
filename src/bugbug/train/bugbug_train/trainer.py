# -*- coding: utf-8 -*-

import lzma
import os
import shutil
from datetime import datetime
from datetime import timedelta
from urllib.request import urlretrieve

from bugbug.models.bug import BugModel
from bugbug.models.component import ComponentModel
from bugbug.models.regression import RegressionModel
from bugbug.models.tracking import TrackingModel

from bugbug_train.secrets import secrets
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from cli_common.utils import ThreadPoolExecutorResult

logger = get_logger(__name__)


class Trainer(object):
    def __init__(self, cache_root, client_id, access_token):
        self.cache_root = cache_root

        assert os.path.isdir(cache_root), 'Cache root {} is not a dir.'.format(cache_root)

        self.client_id = client_id
        self.access_token = access_token

        self.index_service = get_service('index', client_id, access_token)

    def decompress_file(self, path):
        with lzma.open('{}.xz'.format(path), 'rb') as input_f:
            with open(path, 'wb') as output_f:
                shutil.copyfileobj(input_f, output_f)

    def compress_file(self, path):
        with open(path, 'rb') as input_f:
            with lzma.open('{}.xz'.format(path), 'wb') as output_f:
                shutil.copyfileobj(input_f, output_f)

    def train_bug(self):
        logger.info('Training *bug vs feature* model')
        model = BugModel()
        model.train()
        self.compress_file('bugmodel')

    def train_component(self):
        logger.info('Training *component* model')
        model = ComponentModel()
        model.train()
        self.compress_file('componentmodel')

    def train_regression(self):
        logger.info('Training *regression vs non-regression* model')
        model = RegressionModel()
        model.train()
        self.compress_file('regressionmodel')

    def train_tracking(self):
        logger.info('Training *tracking* model')
        model = TrackingModel()
        model.train()
        self.compress_file('trackingmodel')

    def go(self):
        # Download datasets that were built by bugbug_data.
        os.makedirs('data', exist_ok=True)
        with ThreadPoolExecutorResult(max_workers=2) as executor:
            f1 = executor.submit(lambda: urlretrieve('https://index.taskcluster.net/v1/task/project.releng.services.project.testing.bugbug_data.latest/artifacts/public/bugs.json.xz', 'data/bugs.json.xz'))  # noqa
            f1.add_done_callback(lambda f: self.decompress_file('data/bugs.json'))

            f2 = executor.submit(lambda: urlretrieve('https://index.taskcluster.net/v1/task/project.releng.services.project.testing.bugbug_data.latest/artifacts/public/commits.json.xz', 'data/commits.json.xz'))  # noqa
            f2.add_done_callback(lambda f: self.decompress_file('data/commits.json'))

        # Train classifier for bug-vs-nonbug.
        self.train_bug()

        # Train classifier for the component of a bug.
        self.train_component()

        # Train classifier for regression-vs-nonregression.
        self.train_regression()

        # Train classifier for tracking bugs.
        self.train_tracking()

        # Index the task in the TaskCluster index.
        self.index_service.insertTask(
            'project.releng.services.project.{}.bugbug_train.latest'.format(secrets[secrets.APP_CHANNEL]),
            {
                'taskId': os.environ['TASK_ID'],
                'rank': 0,
                'data': {},
                'expires': (datetime.utcnow() + timedelta(31)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        )
