# -*- coding: utf-8 -*-
import json
import os

from cli_common import log

logger = log.get_logger(__name__)


def open_report(report_path):
    '''
    Helper to load and validate a report
    '''
    try:
        assert os.path.exists(report_path), 'Missing file'

        # TODO: move to ijson to reduce loading time
        report = json.load(open(report_path))
        assert isinstance(report, dict), 'Invalid data structure'
    except Exception as e:
        logger.warn('Failed to load report', path=report_path, error=str(e))
        return None

    return report


def get_path_coverage(report, object_path, max_depth=1):
    '''
    Recursively format the paths encountered, adding informations relative
    to file type (file|directory)
    '''
    assert isinstance(report, dict)

    # Find the section from the path
    parts = object_path.split('/')
    for part in filter(None, parts):
        if part not in report['children']:
            raise Exception('Path {} not found in report'.format(object_path))
        report = report['children'][part]

    def _clean_object(obj, base_path, depth=0):
        assert isinstance(obj, dict)
        if 'children' in obj:
            # Directory
            obj['type'] = 'directory'
            obj['path'] = base_path
            if depth >= max_depth:
                obj['children'] = len(obj['children'])
            else:
                obj['children'] = [
                    _clean_object(child, os.path.join(base_path, child_name), depth+1)
                    for child_name, child in obj['children'].items()
                ]
        else:
            # File
            obj['type'] = 'file'
            obj['path'] = base_path
            obj['children'] = None
            if depth >= max_depth:
                del obj['coverage']

        return obj

    return _clean_object(report, object_path)


def get_overall_coverage(report, max_depth=2):
    '''
    Load a covdir report and recursively extract the overall coverage
    of folders until the max depth is reached
    '''
    assert isinstance(report, dict)

    def _extract(obj, base_path='', depth=0):
        if 'children' not in obj or depth > max_depth:
            return {}
        out = {
            base_path:  obj['coveragePercent'],
        }
        for child_name, child in obj['children'].items():
            out.update(_extract(child, os.path.join(base_path, child_name), depth+1))
        return out

    return _extract(report)
