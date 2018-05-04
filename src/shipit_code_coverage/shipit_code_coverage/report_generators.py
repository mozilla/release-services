# -*- coding: utf-8 -*-
import json
import os
import signal
import subprocess
from datetime import datetime

import pytz
import requests

from cli_common.log import get_logger
from shipit_code_coverage import grcov

logger = get_logger(__name__)


class ZeroCov(object):

    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def get_pid_file(self):
        return '/tmp/hgmo.pid'

    def get_pid(self):
        with open(self.get_pid_file(), 'r') as In:
            pid = In.read()
            return int(pid)
        return -1

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

    def kill_hgmo(self):
        pid = self.get_pid()
        os.killpg(os.getpgid(pid), signal.SIGTERM)

    def run_hgmo(self):
        if not os.path.isdir(self.repo_dir):
            logger.warning('Not a directory for m-c', dir=self.repo_dir)
            return False

        oldcwd = os.getcwd()
        os.chdir(self.repo_dir)
        proc = subprocess.Popen(['hg', 'serve',
                                 '--hgmo',
                                 '--daemon',
                                 '--pid-file', self.get_pid_file()])
        proc.wait()
        os.chdir(oldcwd)

        pid = self.get_pid()
        if pid == -1:
            logger.error('hgmo is not running')
            return False

        logger.info('hgmo is running', pid=pid)
        return True

    def get_pushlog(self):
        has_hgmo = self.run_hgmo()
        if has_hgmo:
            url = 'http://localhost:8000/json-pushes'
        else:
            url = 'https://hg.mozilla.org/mozilla-central/json-pushes'

        logger.info('Get pushlog', url=url)

        r = requests.get(url, params={'startID': 0,
                                      'version': 2,
                                      'full': 1})
        if has_hgmo:
            self.kill_hgmo()

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

    def zero_coverage(self, artifacts, out_dir='code-coverage-reports'):
        report = grcov.report(artifacts, out_format='coveralls+')
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

        zero_coverage_report = []
        for fname, functions in zero_coverage_functions.items():
            info = filesinfo[fname]
            info.update({'name': fname,
                         'funcs': len(functions),
                         'uncovered': fname in zero_coverage_files})
            zero_coverage_report.append(info)

            with open(os.path.join(out_dir, 'zero_coverage_functions/%s.json' % fname.replace('/', '_')), 'w') as f:
                json.dump(functions, f)

        with open(os.path.join(out_dir, 'zero_coverage_report.json'), 'w') as f:
            json.dump(zero_coverage_report, f)
