# -*- coding: utf-8 -*-
from shipit_static_analysis.clang import ClangIssue


def test_expanded_macros():
    '''
    Test expanded macros are detected by clang issue
    '''
    parts = ('src/test.cpp', '42', '51', 'error', 'dummy message', 'dummy-check')
    issue = ClangIssue(parts, '/workdir')
    assert issue.is_problem()
    assert issue.line == 42
    assert issue.char == 51
    assert issue.notes == []
    assert issue.is_expanded_macro() is False

    # Add a note starting with "expanded from macro..."
    parts = ('src/test.cpp', '42', '51', 'note', 'expanded from macro Blah dummy.cpp', 'dummy-check-note')
    issue.notes.append(ClangIssue(parts, '/workdir'))
    assert issue.is_expanded_macro() is True

    # Add another note does not change it
    parts = ('src/test.cpp', '42', '51', 'note', 'This is not an expanded macro', 'dummy-check-note')
    issue.notes.append(ClangIssue(parts, '/workdir'))
    assert issue.is_expanded_macro() is True

    # But if we swap them, it does not work anymore
    issue.notes.reverse()
    assert issue.is_expanded_macro() is False
