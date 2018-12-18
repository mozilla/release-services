# -*- coding: utf-8 -*-

import json
import lzma
import os
import shutil
from datetime import datetime
from datetime import timedelta
from urllib.request import urlretrieve

from bugbug import bugzilla
from bugbug.models.bug import BugModel
from bugbug.models.regression import RegressionModel
from bugbug.models.tracking import TrackingModel

from bugbug_eval.secrets import secrets
from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from cli_common.utils import ThreadPoolExecutorResult

logger = get_logger(__name__)


class Evaluator(object):
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

    def is_regression(self, bug):
        return any(keyword in bug['keywords'] for keyword in ['regression', 'talos-regression']) or ('cf_has_regression_range' in bug and bug['cf_has_regression_range'] == 'yes')  # noqa

    def is_feature(self, bug):
        return 'feature' in bug['keywords']

    def is_tracking_decision_made(self, bug):
        for entry in bug['history']:
            for change in entry['changes']:
                if change['field_name'].startswith('cf_tracking_firefox'):
                    if change['added'] in ['blocking', '+', '-']:
                        return True

        return False

    def eval_bug(self):
        results = {}

        model = BugModel.load('bugmodel')
        for bug in bugzilla.get_bugs():
            if self.is_regression(bug):
                results[bug['id']] = True
            elif self.is_feature(bug):
                results[bug['id']] = False
            else:
                results[bug['id']] = True if model.classify(bug)[0] == 1 else False

        with open('bug.json', 'w') as f:
            json.dump(results, f)

    def eval_regression(self):
        results = {}

        model = RegressionModel.load('regressionmodel')
        for bug in bugzilla.get_bugs():
            if self.is_regression(bug):
                results[bug['id']] = True
            elif self.is_feature(bug):
                results[bug['id']] = False
            else:
                results[bug['id']] = True if model.classify(bug)[0] == 1 else False

        with open('regression.json', 'w') as f:
            json.dump(results, f)

    def eval_tracking(self):
        results = []

        model = TrackingModel.load('trackingmodel')
        for bug in bugzilla.get_bugs():
            if self.is_tracking_decision_made(bug):
                continue

            if model.classify(bug)[0] == 1:
                results.append(bug['id'])

        with open('tracking.json', 'w') as f:
            json.dump(results, f)

    def go(self):
        # Download models that were trained by bugbug_train.
        with ThreadPoolExecutorResult(max_workers=3) as executor:
            f1 = executor.submit(lambda: urlretrieve('https://index.taskcluster.net/v1/task/project.releng.services.project.testing.bugbug_train.latest/artifacts/public/bugmodel.xz', 'bugmodel.xz'))  # noqa
            f1.add_done_callback(lambda f: self.decompress_file('bugmodel'))

            f2 = executor.submit(lambda: urlretrieve('https://index.taskcluster.net/v1/task/project.releng.services.project.testing.bugbug_train.latest/artifacts/public/regressionmodel.xz', 'regressionmodel.xz'))  # noqa
            f2.add_done_callback(lambda f: self.decompress_file('regressionmodel'))

            f3 = executor.submit(lambda: urlretrieve('https://index.taskcluster.net/v1/task/project.releng.services.project.testing.bugbug_train.latest/artifacts/public/trackingmodel.xz', 'trackingmodel.xz'))  # noqa
            f3.add_done_callback(lambda f: self.decompress_file('trackingmodel'))

        # Download bugs from the last week that we want to analyze.
        bugzilla.set_token(secrets[secrets.BUGZILLA_TOKEN])

        today = datetime.utcnow()
        one_week_ago = today - timedelta(7)
        bugzilla.download_bugs_between(one_week_ago, today)

        # Eval classifier for bug-vs-nonbug.
        self.eval_bug()

        # Eval classifier for regression-vs-nonregression.
        self.eval_regression()

        # Eval classifier for tracking bugs.
        self.eval_tracking()

        # Index the task in the TaskCluster index.
        self.index_service.insertTask(
            'project.releng.services.project.{}.bugbug_eval.latest'.format(secrets[secrets.APP_CHANNEL]),
            {
                'taskId': os.environ['TASK_ID'],
                'rank': 0,
                'data': {},
                'expires': (datetime.utcnow() + timedelta(31)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
        )
