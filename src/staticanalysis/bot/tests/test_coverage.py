# -*- coding: utf-8 -*-
import os

import responses

from static_analysis_bot.coverage import Coverage


@responses.activate
def test_coverage(mock_config, mock_repository, mock_revision, mock_coverage):
    cov = Coverage()

    mock_revision.files = [
        # Uncovered file
        'my/path/file1.cpp',
        # Covered file
        'my/path/file2.js',
        # Uncovered third-party file
        'test/dummy/thirdparty.c'
    ]

    # Build fake lines.
    for path in mock_revision.files:
        mock_revision.lines[path] = [1]

    # Build fake files.
    for path in mock_revision.files:
        full_path = os.path.join(mock_config.repo_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write('line')

    issues = cov.run(mock_revision)

    # The list must have two elements
    assert len(issues) == 2

    # Verify that each element has a sane value
    issue = issues[0]
    assert issue.path == 'my/path/file1.cpp'
    assert issue.line == 0
    assert issue.message == 'This file is uncovered'
    assert str(issue) == 'my/path/file1.cpp'

    assert not issue.is_third_party()
    assert issue.validates()

    assert issue.as_dict() == {
        'analyzer': 'coverage',
        'path': 'my/path/file1.cpp',
        'line': 0,
        'nb_lines': -1,
        'message': 'This file is uncovered',
        'is_third_party': False,
        'in_patch': True,
        'is_new': False,
        'validates': True,
        'publishable': True,
    }
    assert issue.as_text() == 'This file is uncovered'
    assert issue.as_markdown() == '''
## coverage problem

- **Path**: my/path/file1.cpp
- **Third Party**: no
- **Publishable**: yes

```
This file is uncovered
```
'''

    # Verify that each element has a sane value
    issue = issues[1]
    assert issue.path == 'test/dummy/thirdparty.c'
    assert issue.line == 0
    assert issue.message == 'This file is uncovered'
    assert str(issue) == 'test/dummy/thirdparty.c'

    assert issue.is_third_party()
    assert issue.validates()

    assert issue.as_dict() == {
        'analyzer': 'coverage',
        'path': 'test/dummy/thirdparty.c',
        'line': 0,
        'nb_lines': -1,
        'message': 'This file is uncovered',
        'is_third_party': True,
        'in_patch': True,
        'is_new': False,
        'validates': True,
        'publishable': True,
    }
    assert issue.as_text() == 'This file is uncovered'
    assert issue.as_markdown() == '''
## coverage problem

- **Path**: test/dummy/thirdparty.c
- **Third Party**: yes
- **Publishable**: yes

```
This file is uncovered
```
'''
