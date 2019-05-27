# -*- coding: utf-8 -*-
import pytest


def test_get_path_coverage(mock_covdir_report):
    '''
    Test covdir report parsing to obtain coverage for a specific path
    '''
    from codecoverage_backend import covdir

    # Full coverage
    out = covdir.get_path_coverage(mock_covdir_report, '')
    assert isinstance(out, dict)
    assert out['coveragePercent'] == 85.11
    assert out['linesCovered'] == 267432
    assert out['linesMissed'] == 46779
    assert out['linesTotal'] == 314211
    assert out['name'] == 'src'
    assert out['path'] == ''
    assert out['type'] == 'directory'
    assert len(out['children']) == 12
    assert [c['name'] for c in out['children']] == [
        'builtin',
        'ctypes',
        'frontend',
        'jsapi.cpp',
        'jsdate.cpp',
        'jsexn.cpp',
        'jsexn.h',
        'jsmath.cpp',
        'perf',
        'shell',
        'threading',
        'util',
    ]

    # Subfolder
    out = covdir.get_path_coverage(mock_covdir_report, 'perf')
    assert isinstance(out, dict)
    assert out['coveragePercent'] == 65.45
    assert out['linesCovered'] == 125
    assert out['linesMissed'] == 66
    assert out['linesTotal'] == 191
    assert out['name'] == 'perf'
    assert out['path'] == 'perf'
    assert out['type'] == 'directory'
    assert len(out['children']) == 2
    assert [c['name'] for c in out['children']] == [
        'pm_linux.cpp',
        'pm_stub.cpp',
    ]

    # File
    out = covdir.get_path_coverage(mock_covdir_report, 'perf/pm_linux.cpp')
    assert isinstance(out, dict)
    assert out == {
        'children': None,
        'coverage': [66, 138, 6, -1, -1],
        'coveragePercent': 81.69,
        'linesCovered': 58,
        'linesMissed': 13,
        'linesTotal': 71,
        'name': 'pm_linux.cpp',
        'path': 'perf/pm_linux.cpp',
        'type': 'file'
    }

    # Missing file
    with pytest.raises(Exception) as e:
        covdir.get_path_coverage(mock_covdir_report, 'nope.py')
    assert str(e.value) == 'Path nope.py not found in report'


def test_get_overall_coverage(mock_covdir_report):
    '''
    Test covdir report overall coverage extraction
    '''
    from codecoverage_backend import covdir

    out = covdir.get_overall_coverage(mock_covdir_report, max_depth=1)
    assert out == {
        '': 85.11,
        'builtin': 84.4,
        'ctypes': 80.83,
        'frontend': 78.51,
        'perf': 65.45,
        'shell': 69.95,
        'threading': 90.54,
        'util': 73.29,
    }

    out = covdir.get_overall_coverage(mock_covdir_report, max_depth=2)
    assert out == {
        '': 85.11,
        'builtin': 84.4,
        'builtin/intl': 78.62,
        'ctypes': 80.83,
        'ctypes/libffi': 49.59,
        'frontend': 78.51,
        'perf': 65.45,
        'shell': 69.95,
        'threading': 90.54,
        'util': 73.29
    }
