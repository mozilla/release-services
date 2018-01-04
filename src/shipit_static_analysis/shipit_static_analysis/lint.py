# -*- coding: utf-8 -*-
from shipit_static_analysis import Issue
from cli_common.command import run
from cli_common.log import get_logger
import itertools
import json
import os

logger = get_logger(__name__)

ISSUE_MARKDOWN = '''
## mozlint - {linter}

- **Path**: {path}
- **Level**: {level}
- **Line**: {line}

```
{message}
```
'''


class MozLintIssue(Issue):
    def __init__(self, repo_path, modified_lines, column, level, lineno, linter, message, **kwargs):
        self.nb_lines = 1
        self.path = repo_path
        self.column = column
        self.level = level
        self.line = lineno
        self.linter = linter
        self.message = message
        self.modified_lines = modified_lines

    def __str__(self):
        return '{} issue {} {} line {}'.format(
            self.linter,
            self.level,
            self.path,
            self.line,
        )

    def is_publishable(self):
        '''
        Publishable when line is in modified
        '''
        return self.line in self.modified_lines

    def as_text(self):
        '''
        Build the text content for reporters
        '''
        return '[{}] Linting issue from {} :\n\n{}'.format(self.level, self.linter, self.message)

    def as_markdown(self):
        '''
        Build the Markdown content for debug email
        '''
        return ISSUE_MARKDOWN.format(
            linter=self.linter,
            path=self.path,
            level=self.level,
            line=self.line,
            message=self.message,
        )


class MozLint(object):
    '''
    Exposes mach lint capabilities
    '''
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def run(self, files):
        '''
        List all issues found by mozlint on specified files
        '''
        return list(itertools.chain.from_iterable([
            self.find_issues(path, lines) or []
            for path, lines in files.items()
        ]))

    def find_issues(self, path, modified_lines):
        '''
        Run mozlint through mach, without gecko-env
        '''

        # Run mozlint on a file
        command = [
            './mach', 'lint',
            '-f', 'json',
            path
        ]
        returncode, output, error = run(' '.join(command), cwd=self.repo_dir)
        if returncode == 0:
            logger.debug('No Mozlint errors', path=path)
            return

        # Load output as json
        output = json.loads(output.decode('utf-8'))
        if not output:
            logger.warn('Invalid json output', path=path)
            return
        full_path = os.path.join(self.repo_dir, path)
        if full_path not in output:
            logger.warn('Missing path in linter output', path=path)
            return

        return [
            MozLintIssue(path, modified_lines, **issue)
            for issue in output[full_path]
        ]
