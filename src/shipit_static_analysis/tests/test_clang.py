# -*- coding: utf-8 -*-
from shipit_static_analysis.clang.tidy import ClangTidyIssue
from shipit_static_analysis.clang.format import ClangFormat, ClangFormatIssue

BAD_CPP_OLD = '#include <demo>\nint \tmain(void){\n printf("plop");return 42;    '
BAD_CPP_NEW = '''#include <demo>
int main(void) {
  printf("plop");
  return 42;'''


def test_expanded_macros():
    '''
    Test expanded macros are detected by clang issue
    '''
    parts = ('src/test.cpp', '42', '51', 'error', 'dummy message', 'dummy-check')
    issue = ClangTidyIssue(parts, '/workdir')
    assert issue.is_problem()
    assert issue.line == 42
    assert issue.char == 51
    assert issue.notes == []
    assert issue.is_expanded_macro() is False

    # Add a note starting with "expanded from macro..."
    parts = ('src/test.cpp', '42', '51', 'note', 'expanded from macro Blah dummy.cpp', 'dummy-check-note')
    issue.notes.append(ClangTidyIssue(parts, '/workdir'))
    assert issue.is_expanded_macro() is True

    # Add another note does not change it
    parts = ('src/test.cpp', '42', '51', 'note', 'This is not an expanded macro', 'dummy-check-note')
    issue.notes.append(ClangTidyIssue(parts, '/workdir'))
    assert issue.is_expanded_macro() is True

    # But if we swap them, it does not work anymore
    issue.notes.reverse()
    assert issue.is_expanded_macro() is False


def test_clang_format(tmpdir):
    '''
    Test clang-format runner
    '''

    # Write badly formatted c file
    bad_file = tmpdir.join('bad.cpp')
    bad_file.write('''#include <demo>\nint \tmain(void){\n printf("plop");return 42;    \n}''')

    # Get formatting issues
    cf = ClangFormat(str(tmpdir.realpath()), None)
    issues = cf.run(['bad.cpp', ])

    # Small file, only one issue which group changes
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, ClangFormatIssue)
    assert issue.is_publishable()

    assert issue.path == 'bad.cpp'
    assert issue.line == 1
    assert issue.nb_lines == 3
    assert issue.old == BAD_CPP_OLD
    assert issue.new == BAD_CPP_NEW
