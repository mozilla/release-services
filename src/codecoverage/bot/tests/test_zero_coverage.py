# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

import pytz

from code_coverage_bot.zero_coverage import ZeroCov


def test_zero_coverage(tmpdir,
                       grcov_artifact, grcov_uncovered_artifact,
                       jsvm_artifact, jsvm_uncovered_artifact,
                       grcov_uncovered_function_artifact, jsvm_uncovered_function_artifact,
                       fake_hg_repo_with_contents):
    tmp_path = tmpdir.strpath

    hgrev = '314159265358'
    gitrev = '271828182845'
    ZeroCov(fake_hg_repo_with_contents).generate([
        grcov_artifact, grcov_uncovered_artifact,
        jsvm_artifact, jsvm_uncovered_artifact,
        grcov_uncovered_function_artifact, jsvm_uncovered_function_artifact
    ], hgrev, gitrev, out_dir=tmp_path)

    with open(os.path.join(tmp_path, 'zero_coverage_report.json'), 'r') as f:
        zero_coverage_report = json.load(f)

    assert 'hg_revision' in zero_coverage_report and zero_coverage_report['hg_revision'] == hgrev
    assert 'github_revision' in zero_coverage_report and zero_coverage_report['github_revision'] == gitrev
    assert 'files' in zero_coverage_report
    zero_coverage_functions = zero_coverage_report['files']

    today = datetime.utcnow()
    today = pytz.utc.localize(today)
    today = today.strftime(ZeroCov.DATE_FORMAT)

    expected_zero_coverage_functions = [
        {'funcs': 1, 'name': 'mozglue/build/dummy.cpp', 'uncovered': True,
         'size': 1, 'commits': 2,
         'first_push_date': today, 'last_push_date': today},
        {'funcs': 2, 'name': 'toolkit/components/osfile/osfile.jsm', 'uncovered': False,
         'size': 2, 'commits': 2,
         'first_push_date': today, 'last_push_date': today},
        {'funcs': 1, 'name': 'js/src/jit/JIT.cpp', 'uncovered': False,
         'size': 3, 'commits': 2,
         'first_push_date': today, 'last_push_date': today},
        {'funcs': 1, 'name': 'toolkit/components/osfile/osfile-win.jsm', 'uncovered': True,
         'size': 4, 'commits': 2,
         'first_push_date': today, 'last_push_date': today},
    ]
    assert len(zero_coverage_functions) == len(expected_zero_coverage_functions)
    while len(expected_zero_coverage_functions):
        exp_item = expected_zero_coverage_functions.pop()
        found = False
        for found_item in zero_coverage_functions:
            if found_item['name'] == exp_item['name']:
                found = True
                break
        assert found
        assert found_item['funcs'] == exp_item['funcs']
        assert found_item['first_push_date'] == exp_item['first_push_date']
        assert found_item['last_push_date'] == exp_item['last_push_date']
        assert found_item['size'] == exp_item['size']
        assert found_item['commits'] == exp_item['commits']
        assert found_item['uncovered'] == exp_item['uncovered']
