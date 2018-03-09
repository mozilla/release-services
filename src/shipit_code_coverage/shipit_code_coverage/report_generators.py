# -*- coding: utf-8 -*-
import json
import os

from cli_common.utils import mkdir

from shipit_code_coverage import grcov


def zero_coverage(artifacts, out_dir='code-coverage-reports'):
    report = grcov.report(artifacts, out_format='coveralls+')
    report = json.loads(report.decode('utf-8'))  # Decoding is only necessary until Python 3.6.

    zero_coverage_files = []
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
            zero_coverage_files.append(name)

    with open(os.path.join(out_dir, 'zero_coverage_files.json'), 'w') as f:
        json.dump(zero_coverage_files, f)

    mkdir(os.path.join(out_dir, 'zero_coverage_functions'))

    zero_coverage_function_counts = []
    for fname, functions in zero_coverage_functions.items():
        zero_coverage_function_counts.append({
            'name': fname,
            'funcs': len(functions),
        })
        with open(os.path.join(out_dir, 'zero_coverage_functions/%s.json' % fname.replace('/', '_')), 'w') as f:
            json.dump(functions, f)

    with open(os.path.join(out_dir, 'zero_coverage_functions.json'), 'w') as f:
        json.dump(zero_coverage_function_counts, f)
