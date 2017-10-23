# -*- coding: utf-8 -*-
import os
import difflib
import subprocess
from cli_common.log import get_logger
from shipit_static_analysis.clang import ClangIssue

logger = get_logger(__name__)

OPCODE_REPLACE = 'replace'
OPCODE_INSERT = 'insert'
OPCODE_DELETE = 'delete'
OPCODES = (OPCODE_REPLACE, OPCODE_INSERT, OPCODE_DELETE,)

ISSUE_MARKDOWN = '''
## clang-format

- **Path**: {path}
- **Mode**: {mode}
- **Lines**: from {line}, on {nb_lines} lines

Old lines:

```
{old}
```

New lines:

```
{new}
```
'''


class ClangFormat(object):
    '''
    Clang Format direct Runner
    List potential issues on modified files
    from a patch
    '''
    def __init__(self, work_dir):
        assert os.path.isdir(work_dir)
        self.work_dir = work_dir

    def run(self, modified_lines):
        '''
        Run clang-format on those modified files
        '''
        assert isinstance(modified_lines, dict)
        issues = []
        for path, lines in modified_lines.items():
            issues += self.run_clang_format(path, lines)
        return issues

    def run_clang_format(self, filename, modified_lines):
        '''
        Clang-format is very fast, no need for a worker queue here
        '''
        full_path = os.path.join(self.work_dir, filename)
        assert os.path.exists(full_path), \
            'Modified file not found {}'.format(full_path)

        # Build command line for a filename
        cmd = [
            # Use system clang format
            'clang-format',

            # Use style from directories
            '-style=file',

            full_path,
        ]
        logger.info('Running clang-format', cmd=' '.join(cmd))

        # Run command
        clang_output = subprocess.check_output(cmd, cwd=self.work_dir)

        # Compare output with original file
        src_lines = [x.rstrip('\n') for x in open(full_path).readlines()]
        clang_lines = clang_output.decode('utf-8').split('\n')

        # Build issues from diff of diff !
        diff = difflib.SequenceMatcher(
            a=src_lines,
            b=clang_lines,
        )
        return [
            ClangFormatIssue(filename, src_lines, clang_lines, modified_lines, *opcode)
            for opcode in diff.get_opcodes()
            if opcode[0] in OPCODES
        ]


class ClangFormatIssue(ClangIssue):
    '''
    An issue created by Clang Format tool
    '''
    def __init__(self, path, a, b, modified_lines, mode, i1, i2, j1, j2):
        assert mode in OPCODES
        assert isinstance(i1, int)
        assert isinstance(i2, int)
        assert isinstance(j1, int)
        assert isinstance(j2, int)
        self.path = path
        self.mode = mode

        # Lines used to make the diff
        # replace: a[i1:i2] should be replaced by b[j1:j2].
        # delete: a[i1:i2] should be deleted.
        # insert: b[j1:j2] should be inserted at a[i1:i1].
        # These indexes are starting from 1
        # need to offset them
        self.old = '\n'.join(a[i1 - 1:i2])
        self.new = self.mode != OPCODE_DELETE and '\n'.join(b[j1 - 1:j2])

        # i1 is alsways the starting point
        self.line = i1
        if self.mode == OPCODE_INSERT:
            self.nb_lines = 1
        else:
            assert i2 > i1
            self.nb_lines = i2 - i1 + 1

        # Detect if isssue is in the patch
        lines = set(range(self.line, self.line + self.nb_lines))
        self.in_patch = not lines.isdisjoint(modified_lines)

    def __str__(self):
        return 'clang-format issue {} {} line {}-{}'.format(
            self.path,
            self.mode,
            self.line,
            self.nb_lines,
        )

    def is_publishable(self):
        '''
        Publish issues when they affect a line in the patch
        '''
        return self.in_patch

    @property
    def mozreview_body(self):
        '''
        Build the text body published on MozReview
        According to diff mode
        '''
        if self.mode == OPCODE_REPLACE:
            return 'Replace by: \n\n```\n{}\n```'.format(self.new)

        elif self.mode == OPCODE_INSERT:
            return 'Insert at this line: \n\n```\n{}\n```'.format(self.new)

        elif self.mode == OPCODE_DELETE:
            if self.nb_lines > 1:
                return 'Delete these {} lines'.format(self.nb_lines)
            return 'Delete this line.'

        else:
            raise Exception('Unsupported mode')

    def as_markdown(self):
        '''
        Build the Markdown content for debug email
        '''
        return ISSUE_MARKDOWN.format(
            path=self.path,
            mode=self.mode,
            line=self.line,
            nb_lines=self.nb_lines,
            old=self.old,
            new=self.new,
        )
