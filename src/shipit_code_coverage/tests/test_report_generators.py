# -*- coding: utf-8 -*-
import json
import os
import shutil
import time
from datetime import datetime

import hglib

from shipit_code_coverage import report_generators


def create_fake_repo(tmp):

    def tobytes(x):
        return bytes(x, 'ascii')

    dest = os.path.join(tmp, 'repos')
    local = os.path.join(dest, 'local')
    remote = os.path.join(dest, 'remote')
    for d in [local, remote]:
        os.makedirs(d)
        hglib.init(d)

    oldcwd = os.getcwd()
    os.chdir(local)
    hg = hglib.open(local)

    files = [{'name': 'mozglue/build/dummy.cpp',
              'size': 1},
             {'name': 'toolkit/components/osfile/osfile.jsm',
              'size': 2},
             {'name': 'js/src/jit/JIT.cpp',
              'size': 3},
             {'name': 'toolkit/components/osfile/osfile-win.jsm',
              'size': 4}]

    for c in '?!':
        for f in files:
            fname = f['name']
            parent = os.path.dirname(fname)
            if not os.path.exists(parent):
                os.makedirs(parent)
            with open(fname, 'w') as Out:
                Out.write(c * f['size'])
            hg.add(files=[tobytes(fname)])
            hg.commit(message='Commit file {} with {} inside'.format(fname, c),
                      user='Moz Illa <milla@mozilla.org>')
            hg.push(dest=tobytes(remote))
            time.sleep(1.01)

    hg.close()
    os.chdir(oldcwd)

    shutil.copyfile(os.path.join(remote, '.hg/pushlog2.db'),
                    os.path.join(local, '.hg/pushlog2.db'))

    return local


def get_date(s):
    return datetime.strptime(s, report_generators.ZeroCov.DATE_FORMAT)


def test_zero_coverage(tmpdir,
                       grcov_artifact, grcov_uncovered_artifact,
                       jsvm_artifact, jsvm_uncovered_artifact,
                       grcov_uncovered_function_artifact, jsvm_uncovered_function_artifact):
    tmp_path = tmpdir.strpath
    fake_repo = create_fake_repo(tmp_path)

    report_generators.ZeroCov(fake_repo).zero_coverage([
        grcov_artifact, grcov_uncovered_artifact,
        jsvm_artifact, jsvm_uncovered_artifact,
        grcov_uncovered_function_artifact, jsvm_uncovered_function_artifact
    ], out_dir=tmp_path)

    with open(os.path.join(tmp_path, 'zero_coverage_functions/mozglue_build_dummy.cpp.json'), 'r') as f:
        assert set(json.load(f)) == set(['main'])
    with open(os.path.join(tmp_path, 'zero_coverage_functions/js_src_jit_JIT.cpp.json'), 'r') as f:
        assert set(json.load(f)) == set(['anUncoveredFunction'])
    with open(os.path.join(tmp_path, 'zero_coverage_functions/toolkit_components_osfile_osfile.jsm.json'), 'r') as f:
        assert set(json.load(f)) == set(['read', 'write'])

    with open(os.path.join(tmp_path, 'zero_coverage_report.json'), 'r') as f:
        zero_coverage_functions = json.load(f)

    expected_zero_coverage_functions = [
        {'funcs': 1, 'name': 'mozglue/build/dummy.cpp', 'uncovered': True,
         'size': 1, 'commits': 2,
         'first_push_date': '', 'last_push_date': ''},
        {'funcs': 2, 'name': 'toolkit/components/osfile/osfile.jsm', 'uncovered': False,
         'size': 2, 'commits': 2,
         'first_push_date': '', 'last_push_date': ''},
        {'funcs': 1, 'name': 'js/src/jit/JIT.cpp', 'uncovered': False,
         'size': 3, 'commits': 2,
         'first_push_date': '', 'last_push_date': ''},
        {'funcs': 1, 'name': 'toolkit/components/osfile/osfile-win.jsm', 'uncovered': True,
         'size': 4, 'commits': 2,
         'first_push_date': '', 'last_push_date': ''},
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
        assert get_date(found_item['last_push_date']) > get_date(found_item['first_push_date'])
        assert found_item['size'] == exp_item['size']
        assert found_item['commits'] == exp_item['commits']
