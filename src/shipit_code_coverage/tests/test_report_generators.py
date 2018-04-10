# -*- coding: utf-8 -*-
import json
import os

from shipit_code_coverage import report_generators


def test_zero_coverage(tmpdir,
                       grcov_artifact, grcov_uncovered_artifact,
                       jsvm_artifact, jsvm_uncovered_artifact,
                       grcov_uncovered_function_artifact, jsvm_uncovered_function_artifact):
    tmp_path = tmpdir.strpath

    report_generators.zero_coverage([
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
        {'funcs': 1, 'name': 'mozglue/build/dummy.cpp', 'uncovered': True},
        {'funcs': 2, 'name': 'toolkit/components/osfile/osfile.jsm', 'uncovered': False},
        {'funcs': 1, 'name': 'js/src/jit/JIT.cpp', 'uncovered': False},
        {'funcs': 1, 'name': 'toolkit/components/osfile/osfile-win.jsm', 'uncovered': True},
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
