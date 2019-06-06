# -*- coding: utf-8 -*-
import pytest


def test_open_report(tmpdir, mock_covdir_report):
    '''
    Test opening reports
    '''
    from codecoverage_backend import covdir

    empty = tmpdir.join('empty.json')
    assert covdir.open_report(empty.realpath()) is None

    bad = tmpdir.join('bad.json')
    bad.write('not json')
    assert covdir.open_report(bad.realpath()) is None

    invalid = tmpdir.join('invalid.json')
    invalid.write('"string"')
    assert covdir.open_report(invalid.realpath()) is None

    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    assert isinstance(report, dict)

    assert list(report.keys()) == ['children', 'coveragePercent', 'linesCovered', 'linesMissed', 'linesTotal', 'name']


def test_get_path_coverage(mock_covdir_report):
    '''
    Test covdir report parsing to obtain coverage for a specific path
    '''
    from codecoverage_backend import covdir

    # Full coverage
    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    out = covdir.get_path_coverage(report, '')
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
    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    out = covdir.get_path_coverage(report, 'perf')
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
    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    out = covdir.get_path_coverage(report, 'perf/pm_linux.cpp')
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
        report = covdir.open_report(mock_covdir_report)
        assert report is not None
        covdir.get_path_coverage(report, 'nope.py')
    assert str(e.value) == 'Path nope.py not found in report'


def test_get_overall_coverage(mock_covdir_report):
    '''
    Test covdir report overall coverage extraction
    '''
    from codecoverage_backend import covdir

    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    out = covdir.get_overall_coverage(report, max_depth=1)
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

    report = covdir.open_report(mock_covdir_report)
    assert report is not None
    out = covdir.get_overall_coverage(report, max_depth=2)
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
