# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

import pytz
import requests

from cli_common.log import get_logger
from codecoverage_bot import grcov
from codecoverage_bot import hgmo

logger = get_logger(__name__)


class ZeroCov(object):

    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, repo_dir):
        assert os.path.isdir(repo_dir), '{} is not a directory'.format(repo_dir)
        self.repo_dir = repo_dir

    def get_file_size(self, filename):
        if self.repo_dir:
            filename = os.path.join(self.repo_dir, filename)
            if os.path.isfile(filename):
                return os.path.getsize(filename)
        return 0

    def get_utc_from_timestamp(self, ts):
        d = datetime.utcfromtimestamp(ts)
        return d.replace(tzinfo=pytz.utc)

    def get_date_str(self, d):
        return d.strftime(ZeroCov.DATE_FORMAT)

    def get_pushlog(self):
        with hgmo.HGMO(self.repo_dir) as url:
            url += '/json-pushes'
            logger.info('Get pushlog', url=url)
            r = requests.get(url, params={'startID': 0,
                                          'version': 2,
                                          'full': 1})

        if not r.ok:
            logger.error('Pushlog cannot be retrieved', url=r.url, status_code=r.status_code)
            return {}

        logger.info('Pushlog retrieved')

        return r.json()

    def get_fileinfo(self, filenames):
        pushlog = self.get_pushlog()
        if not pushlog:
            return {}

        res = {}
        filenames = set(filenames)
        for push in pushlog['pushes'].values():
            pushdate = self.get_utc_from_timestamp(push['date'])
            for chgset in push['changesets']:
                for f in chgset['files']:
                    if f not in filenames:
                        continue

                    if f not in res:
                        res[f] = {'size': self.get_file_size(f),
                                  'first_push_date': pushdate,
                                  'last_push_date': pushdate,
                                  'commits': 1}
                    else:
                        r = res[f]
                        if pushdate < r['first_push_date']:
                            r['first_push_date'] = pushdate
                        elif pushdate > r['last_push_date']:
                            r['last_push_date'] = pushdate
                        r['commits'] += 1

        # stringify the pushdates
        for v in res.values():
            v['first_push_date'] = self.get_date_str(v['first_push_date'])
            v['last_push_date'] = self.get_date_str(v['last_push_date'])

        # add default data for files which are not in res
        for f in filenames:
            if f in res:
                continue
            res[f] = {'size': 0,
                      'first_push_date': '',
                      'last_push_date': '',
                      'commits': 0}

        return res

    def generate(self, artifacts, hgrev, gitrev, out_dir='.'):
        report = grcov.report(artifacts, out_format='coveralls+', source_dir=self.repo_dir)
        report = json.loads(report.decode('utf-8'))  # Decoding is only necessary until Python 3.6.

        zero_coverage_files = set()
        zero_coverage_functions = {}
        for sf in report['source_files']:
            name = sf['name']

            # For C/C++ source files, we can consider a file as being uncovered
            # when all its source lines are uncovered.
            all_lines_uncovered = all(c is None or c == 0 for c in sf['coverage'])
            # For JavaScript files, we can't do the same, as the top-level is always
            # executed, even if it just contains declarations. So, we need to check if
            # all its functions, except the top-level, are uncovered.
            all_functions_uncovered = True
            for f in sf['functions']:
                f_name = f['name']
                if f_name == 'top-level':
                    continue

                if not f['exec']:
                    if name in zero_coverage_functions:
                        zero_coverage_functions[name].append(f['name'])
                    else:
                        zero_coverage_functions[name] = [f['name']]
                else:
                    all_functions_uncovered = False

            if all_lines_uncovered or (len(sf['functions']) > 1 and all_functions_uncovered):
                zero_coverage_files.add(name)

        os.makedirs(os.path.join(out_dir, 'zero_coverage_functions'), exist_ok=True)

        filesinfo = self.get_fileinfo(zero_coverage_functions.keys())

        zero_coverage_info = []
        for fname, functions in zero_coverage_functions.items():
            info = filesinfo[fname]
            info.update({'name': fname,
                         'funcs': len(functions),
                         'uncovered': fname in zero_coverage_files})
            zero_coverage_info.append(info)

        zero_coverage_report = {'github_revision': gitrev,
                                'hg_revision': hgrev,
                                'files': zero_coverage_info}

        with open(os.path.join(out_dir, 'zero_coverage_report.json'), 'w') as f:
            json.dump(zero_coverage_report, f)
