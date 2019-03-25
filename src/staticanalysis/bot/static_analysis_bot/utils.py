# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import tempfile
from contextlib import contextmanager


@contextmanager
def build_temp_file(content, suffix):
    '''
    Build a temporary file and remove it after usage
    '''
    assert isinstance(content, str)
    assert isinstance(suffix, str)

    # Write patch in tmp
    _, path = tempfile.mkstemp(suffix=suffix)
    with open(path, 'w') as f:
        f.write(content)

    yield path

    # Cleanup
    os.unlink(path)


def is_lint_issue(issue):
    '''
    Check the input is a lint issue compatible with
    https://phabricator.services.mozilla.com/conduit/method/harbormaster.sendmessage/
    '''
    assert isinstance(issue, dict)

    # Check required keys
    for key in ('name', 'code', 'severity', 'path'):
        value = issue.get(key)
        assert value is not None, 'Missing key {}'.format(key)
        assert isinstance(value, str), '{} should be a string'.format(key)

    # Check the severity is a valid value
    assert issue['severity'] in ('advice', 'autofix', 'warning', 'error', 'disabled'), \
        'Invalid severity value: {}'.format(issue['severity'])

    # Check optional integers
    for key in ('line', 'char'):
        value = issue.get(key)
        if value:
            assert isinstance(value, int), '{} should be an int'.format(key)

    return True
