# -*- coding: utf-8 -*-
import collections
import json
import os
from datetime import datetime

import pytz

from cli_common.log import get_logger
from code_coverage_bot import grcov
from code_coverage_bot import hgmo

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
        with hgmo.HGMO(self.repo_dir) as hgmo_server:
            pushlog = hgmo_server.get_pushes(startID=0)

        logger.info('Pushlog retrieved')

        return pushlog

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

    def generate_zero_coverage_some_platform_only(self, platforms_artifacts, hgrev, gitrev, out_dir='.'):
        '''
        :param platforms_artifacts: dictionary with key platform name, and value is list of artifacts
        :param hgrev: hg revision, must be same for all reports
        :param gitrev: git revision, must be same for all reports
        :param out_dir: directory to output the json result
        '''

        platforms = ['linux', 'windows']

        # mapping file_name -> set of platforms uncovered
        uncovered_map = collections.defaultdict(lambda: set())
        platform_files = collections.defaultdict(lambda: set())
        zero_coverage_files = {}

        for platform in platforms:
            assert platform in platforms_artifacts

            artifacts = platforms_artifacts[platform]

            # to get all files in the artifacts
            report = grcov.report(artifacts, out_format='coveralls+', source_dir=self.repo_dir)
            report = json.loads(report.decode('utf-8'))
            platform_files[platform] = {x['name'] for x in report['source_files']}

            # to get zero coverage files
            zero_coverage_report = self.generate(artifacts, hgrev, gitrev, out_dir=out_dir, writeout_result=False)
            for file_info in zero_coverage_report['files']:
                zero_coverage_files[file_info['name']] = file_info

                if file_info['uncovered'] is True:
                    uncovered_map[file_info['name']].add(platform)

        # for each zero coverage files, check if the file exist on other platform but is covered
        zero_coverage_info = []
        for fname, info in zero_coverage_files.items():
            # skip covered files
            if not uncovered_map[fname]:
                continue

            # skip file that is uncovered on all platform where file exist
            platform_file_exist = {x for x in platforms if fname in platform_files[x]}
            covered = list(platform_file_exist - uncovered_map[fname])
            if not covered:
                continue

            uncovered = list(uncovered_map[fname])
            info.update({
                'covered_platforms': covered,
                'uncovered_platforms': uncovered,
            })
            del info['uncovered']
            zero_coverage_info.append(info)

        zero_coverage_report = {
            'github_revision': gitrev,
            'hg_revision': hgrev,
            'files': zero_coverage_info
        }

        os.makedirs(os.path.join(out_dir, 'zero_coverage_some_platform_functions'), exist_ok=True)
        with open(os.path.join(out_dir, 'zero_coverage_some_platform_functions_report.json'), 'w') as f:
            json.dump(zero_coverage_report, f)

    def generate(self, artifacts, hgrev, gitrev, out_dir='.', writeout_result=True):
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

        if writeout_result is True:
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

        if writeout_result is True:
            with open(os.path.join(out_dir, 'zero_coverage_report.json'), 'w') as f:
                json.dump(zero_coverage_report, f)
        return zero_coverage_report
