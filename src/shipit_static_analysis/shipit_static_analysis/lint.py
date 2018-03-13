# -*- coding: utf-8 -*-
from shipit_static_analysis import Issue, stats
from shipit_static_analysis.revisions import Revision
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
- **Third Party**: {third_party}
- **Disabled rule**: {disabled_rule}
- **Publishable**: {publishable}

```
{message}
```
'''


class MozLintIssue(Issue):
    def __init__(self, repo_dir, repo_path, column, level, lineno, linter, message, rule, **kwargs):
        self.nb_lines = 1
        self.repo_dir = repo_dir
        self.path = repo_path
        self.column = column
        self.level = level
        self.line = lineno
        self.linter = linter
        self.message = message
        self.rule = rule

    def __str__(self):
        return '{} issue {} {} line {}'.format(
            self.linter,
            self.level,
            self.path,
            self.line,
        )

    def is_disabled_rule(self):
        '''
        Some rules are disabled:
        * Python "bad" quotes
        '''

        # See https://github.com/mozilla-releng/services/issues/777
        if self.linter == 'flake8' and self.rule == 'Q000':
            return True

        return False

    def is_publishable(self):
        '''
        Publishable when:
        * file is not 3rd party
        * rule is not disabled
        '''
        return not self.is_third_party() and not self.is_disabled_rule()

    def as_text(self):
        '''
        Build the text content for reporters
        '''
        return '{}: {} [{}: {}]'.format(
            self.level.capitalize(),
            self.message.capitalize(),
            self.linter,
            self.rule,
        )

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
            third_party=self.is_third_party() and 'yes' or 'no',
            publishable=self.is_publishable() and 'yes' or 'no',
            disabled_rule=self.is_disabled_rule() and 'yes' or 'no',
        )


class MozLint(object):
    '''
    Exposes mach lint capabilities
    '''
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

        # Check we have a Shell set in env
        # This is needed for mach + mozlint execution
        assert 'SHELL' in os.environ, \
            'Missing SHELL environment variable'

    @stats.api.timed('runtime.mozlint')
    def run(self, revision):
        '''
        List all issues found by mozlint on specified files
        '''
        assert isinstance(revision, Revision)

        issues = list(itertools.chain.from_iterable([
            self.find_issues(path) or []
            for path in revision.files
        ]))

        stats.report_issues('mozlint', issues)

        return issues

    def find_issues(self, path):
        '''
        Run mozlint through mach, using gecko-env
        '''

        # Run mozlint on a file
        command = [
            'gecko-env',
            './mach', 'lint',
            '-f', 'json',
            '--quiet',
            path
        ]
        returncode, output, error = run(' '.join(command), cwd=self.repo_dir)
        if returncode == 0:
            logger.debug('No Mozlint errors', path=path)
            return

        # Load output as json
        # Only consider last line, as ./mach lint may output
        # linter setup output on stdout :/
        try:
            lines = list(filter(None, output.decode('utf-8').split('\n')))
            payload = json.loads(lines[-1])
        except json.decoder.JSONDecodeError:
            logger.warn('Invalid json output', path=path, lines=lines)
            raise

        full_path = os.path.join(self.repo_dir, path)
        if full_path not in payload and path not in payload:
            logger.warn('Missing path in linter output', path=path)
            return

        # Mozlint uses both full & relative path to index issues
        return [
            MozLintIssue(self.repo_dir, path, **issue)
            for p in (path, full_path)
            for issue in payload.get(p, [])
        ]
