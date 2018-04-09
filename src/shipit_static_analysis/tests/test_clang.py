# -*- coding: utf-8 -*-

BAD_CPP_SRC = '''#include <demo>
int \tmain(void){
 printf("plop");return 42;
}'''

BAD_CPP_DIFF = '''1,3c1,4
< #include <demo>
< int \tmain(void){
<  printf("plop");return 42;
---
> #include <demo>
> int main(void) {
>   printf("plop");
>   return 42;
'''

BAD_CPP_VALID = '''#include <demo>
int main(void) {
  printf("plop");
  return 42;
}'''

BAD_CPP_TIDY = '''
void assignment() {
  char *a = 0;
  char x = 0;
}

int *ret_ptr() {
  return 0;
}
'''


def test_expanded_macros(mock_stats):
    '''
    Test expanded macros are detected by clang issue
    '''
    from shipit_static_analysis.clang.tidy import ClangTidyIssue
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


def test_clang_format(mock_repository, mock_stats, mock_clang, mock_revision):
    '''
    Test clang-format runner
    '''
    from shipit_static_analysis.clang.format import ClangFormat, ClangFormatIssue

    # Write badly formatted c file
    bad_file = mock_repository.directory.join('bad.cpp')
    bad_file.write(BAD_CPP_SRC)

    # Get formatting issues
    cf = ClangFormat(str(mock_repository.directory.realpath()))
    mock_revision.files = ['bad.cpp', ]
    mock_revision.lines = {
        'bad.cpp': [1, 2, 3],
    }
    issues = cf.run(mock_revision)

    # Small file, only one issue which group changes
    assert isinstance(issues, list)
    assert len(issues) == 1
    issue = issues[0]
    assert isinstance(issue, ClangFormatIssue)
    assert issue.is_publishable()

    assert issue.path == 'bad.cpp'
    assert issue.line == 1
    assert issue.nb_lines == 3
    assert issue.as_diff() == BAD_CPP_DIFF

    # At the end of the process, original file is patched
    assert bad_file.read() == BAD_CPP_VALID

    # Test stats
    mock_stats.flush()
    metrics = mock_stats.get_metrics('issues.clang-format')
    assert len(metrics) == 1
    assert metrics[0][1]

    metrics = mock_stats.get_metrics('issues.clang-format.publishable')
    assert len(metrics) == 1
    assert metrics[0][1]

    metrics = mock_stats.get_metrics('runtime.clang-format.avg')
    assert len(metrics) == 1
    assert metrics[0][1] > 0


def test_clang_tidy(mock_repository, mock_config, mock_clang, mock_stats, mock_revision):
    '''
    Test clang-tidy runner
    '''
    from shipit_static_analysis.clang.tidy import ClangTidy, ClangTidyIssue

    # Init clang tidy runner
    repo_dir = mock_repository.directory
    build_dir = repo_dir.mkdir('../build')
    ct = ClangTidy(
        str(repo_dir.realpath()),
        str(build_dir.realpath())
    )

    # Write dummy 3rd party file
    third_party = repo_dir.join(mock_config.third_party)
    third_party.write('test/dummy')

    # Write badly formatted c file
    bad_file = repo_dir.join('bad.cpp')
    bad_file.write(BAD_CPP_TIDY)

    # Get issues found by clang-tidy
    mock_revision.files = ['bad.cpp', ]
    mock_revision.lines = {
        'bad.cpp': range(len(BAD_CPP_TIDY.split('\n'))),
    }
    issues = ct.run(mock_revision)
    assert len(issues) == 2
    assert isinstance(issues[0], ClangTidyIssue)
    assert issues[0].check == 'modernize-use-nullptr'
    assert issues[0].line == 3
    assert isinstance(issues[1], ClangTidyIssue)
    assert issues[1].check == 'modernize-use-nullptr'
    assert issues[1].line == 8

    # Test stats
    mock_stats.flush()
    metrics = mock_stats.get_metrics('issues.clang-tidy')
    assert len(metrics) == 1
    assert metrics[0][1] == 2

    metrics = mock_stats.get_metrics('issues.clang-tidy.publishable')
    assert len(metrics) == 1
    assert metrics[0][1] == 2

    metrics = mock_stats.get_metrics('runtime.clang-tidy.avg')
    assert len(metrics) == 1
    assert metrics[0][1] > 0


def test_clang_tidy_checks(mock_repository, mock_clang):
    '''
    Test that all our clang-tidy checks actually exist
    '''
    from shipit_static_analysis.clang.tidy import ClangTidy
    from shipit_static_analysis.config import CONFIG_URL, settings

    # Get the set of all available checks that the local clang-tidy offers
    repo_dir = mock_repository.directory
    clang_tidy = ClangTidy(
        str(repo_dir.realpath()),
        validate_checks=False,
    )

    # Verify that Firefox's clang-tidy configuration actually specifies checks
    assert len(settings.clang_checkers) > 0, \
        'Firefox clang-tidy configuration {} should specify > 0 clang_checkers'.format(CONFIG_URL)

    # Verify that the specified clang-tidy checks actually exist
    missing = clang_tidy.list_missing_checks()
    assert len(missing) == 0, \
        'Missing clang-tidy checks: {}'.format(', '.join(missing))
