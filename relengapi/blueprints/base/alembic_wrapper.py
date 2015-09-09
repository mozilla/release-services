from __future__ import absolute_import

import logging
import os

from alembic import command
from alembic.config import Config as AlembicConfig
from flask import current_app

import relengapi
from relengapi.lib import subcommands

logger = logging.getLogger(__name__)


class Config(AlembicConfig):
    def get_template_directory(self):
        alembic_dir = os.path.join(os.path.dirname(relengapi.__file__), 'alembic')
        return os.path.join(alembic_dir, 'templates')


def _get_config(directory):
    config_path = os.path.join(directory, 'alembic.ini')
    if not os.path.isfile(config_path):
        logger.error("Configuration file does not exist in %s", directory)
        quit()
    config = Config(config_path)
    config.set_main_option('script_location', directory)
    return config


class AlembicSubcommand(subcommands.Subcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser(
            'alembic', help='Wrapper for alembic commands')
        parser.add_argument('dbname', default=None,
                            help='Name of the database to interact with')
        parser.add_argument('-d', '--directory', dest='base_directory',
                            default=os.path.join(os.path.dirname(relengapi.__file__), 'alembic'),
                            help="base alembic directory, where the migrations folder lives")
        subparsers = parser.add_subparsers()
        cmds = [cls() for cls in AlembicSubcommand.__subclasses__()]
        for cmd in cmds:
            subparser = cmd.make_parser(subparsers)
            subparser.set_defaults(_alembic_subcommands=cmd)
        return parser

    def run(self, parser, args):
        if args.dbname not in current_app.db.database_names:
            logger.error("You must specify a valid database name")
            return
        args.directory = os.path.join(args.base_directory, args.dbname)
        args._alembic_subcommands.run(parser, args)


class AlembicInitSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('init', help=self.init.__doc__)
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help="migration script directory (default is 'migrations')")
        return parser

    def run(self, parser, args):
        self.init(**vars(args))

    def init(self, directory, **kwargs):
        """Generates a new migration"""
        config = Config()
        config.set_main_option('script_location', directory)
        config.config_file_name = os.path.join(directory, 'alembic.ini')
        command.init(config, directory, 'relengapi')


class AlembicRevisionSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('revision', help=self.revision.__doc__)
        parser.add_argument('--rev-id', dest='rev_id', default=None,
                            help=('Specify a hardcoded revision id instead of '
                                  'generating one'))
        parser.add_argument('--version-path', dest='version_path', default=None,
                            help=('Specify specific path from config for version '
                                  'file'))
        parser.add_argument('--branch-label', dest='branch_label', default=None,
                            help=('Specify a branch label to apply to the new '
                                  'revision'))
        parser.add_argument('--splice', dest='splice', action='store_true',
                            default=False,
                            help=('Allow a non-head revision as the "head" to '
                                  'splice onto'))
        parser.add_argument('--head', dest='head', default='head',
                            help=('Specify head revision or <branchname>@head to '
                                  'base new revision on'))
        parser.add_argument('--sql', dest='sql', action='store_true', default=False,
                            help=("Don't emit SQL to database - dump to standard "
                                  "output instead"))
        parser.add_argument('--autogenerate', dest='autogenerate',
                            action='store_true', default=False,
                            help=('Populate revision script with candidate migration '
                                  'operation, based on comparison of database to '
                                  'model'))
        parser.add_argument('-m', '--message', dest='message', default=None)
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.revision(**vars(args))

    def revision(self, directory=None, message=None, autogenerate=False, sql=False,
                 head='head', splice=False, branch_label=None, version_path=None,
                 rev_id=None, **kwargs):
        """Create a new revision file."""
        config = _get_config(directory)
        command.revision(config, message, autogenerate=autogenerate, sql=sql,
                         head=head, splice=splice, branch_label=branch_label,
                         version_path=version_path, rev_id=rev_id)


class AlembicMigrateSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('migrate', help=self.migrate.__doc__)
        parser.add_argument('--rev-id', dest='rev_id', default=None,
                            help=('Specify a hardcoded revision id instead of '
                                  'generating one'))
        parser.add_argument('--version-path', dest='version_path', default=None,
                            help=('Specify specific path from config for version '
                                  'file'))
        parser.add_argument('--branch-label', dest='branch_label', default=None,
                            help=('Specify a branch label to apply to the new '
                                  'revision'))
        parser.add_argument('--splice', dest='splice', action='store_true',
                            default=False,
                            help=('Allow a non-head revision as the "head" to '
                                  'splice onto'))
        parser.add_argument('--head', dest='head', default='head',
                            help=('Specify head revision or <branchname>@head to '
                                  'base new revision on'))
        parser.add_argument('--sql', dest='sql', action='store_true', default=False,
                            help=("Don't emit SQL to database - dump to standard "
                                  "output instead"))
        parser.add_argument('-m', '--message', dest='message', default=None)
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.migrate(**vars(args))

    def migrate(self, directory=None, message=None, sql=False, head='head', splice=False,
                branch_label=None, version_path=None, rev_id=None, **kwargs):  # pragma: no cover
        """Alias for 'revision --autogenerate'"""
        config = _get_config(directory)
        command.revision(config, message, autogenerate=True, sql=sql, head=head,
                         splice=splice, branch_label=branch_label,
                         version_path=version_path, rev_id=rev_id)


class AlembicMergeSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('merge', help=self.merge.__doc__)
        parser.add_argument('--rev-id', dest='rev_id', default=None,
                            help=('Specify a hardcoded revision id instead of '
                                  'generating one'))
        parser.add_argument('--branch-label', dest='branch_label', default=None,
                            help=('Specify a branch label to apply to the new '
                                  'revision'))
        parser.add_argument('-m', '--message', dest='message', default=None)
        parser.add_argument('revisions',
                            help='one or more revisions, or "heads" for all heads')
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.merge(**vars(args))

    def merge(self, directory=None, revisions='', message=None, branch_label=None,
              rev_id=None, **kwargs):  # pragma: no cover
        """Merge two revisions together.  Creates a new migration file"""
        config = _get_config(directory)
        command.merge(config, revisions, message=message,
                      branch_label=branch_label, rev_id=rev_id)


class AlembicUpgradeSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('upgrade', help=self.upgrade.__doc__)
        parser.add_argument('--tag', dest='tag', default=None,
                            help=("Arbitrary 'tag' name - can be used by custom "
                                  "env.py scripts"))
        parser.add_argument('--sql', dest='sql', action='store_true', default=False,
                            help=("Don't emit SQL to database - dump to standard "
                                  "output instead"))
        parser.add_argument('revision', nargs='?', default='head',
                            help="revision identifier")
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.upgrade(**vars(args))

    def upgrade(self, directory=None, revision='head', sql=False, tag=None,
                **kwargs):  # pragma: no cover
        """Upgrade to a later version"""
        config = _get_config(directory)
        command.upgrade(config, revision, sql=sql, tag=tag)


class AlembicDowngradeSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('downgrade', help=self.downgrade.__doc__)
        parser.add_argument('--tag', dest='tag', default=None,
                            help=("Arbitrary 'tag' name - can be used by custom "
                                  "env.py scripts"))
        parser.add_argument('--sql', dest='sql', action='store_true', default=False,
                            help=("Don't emit SQL to database - dump to standard "
                                  "output instead"))
        parser.add_argument('revision', nargs='?', default="-1",
                            help="revision identifier")
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.downgrade(**vars(args))

    def downgrade(self, directory=None, revision='-1', sql=False, tag=None,
                  **kwargs):  # pragma: no cover
        """Revert to a previous version"""
        config = _get_config(directory)
        if sql and revision == '-1':
            revision = 'head:-1'
        command.downgrade(config, revision, sql=sql, tag=tag)


class AlembicShowSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('show', help=self.show.__doc__)
        parser.add_argument('revision', nargs='?', default="head",
                            help="revision identifier")
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.show(**vars(args))

    def show(self, directory=None, revision='head', **kwargs):  # pragma: no cover
        """Show the revision denoted by the given symbol."""
        config = _get_config(directory)
        command.show(config, revision)


class AlembicHistorySubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('history', help=self.history.__doc__)
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                            default=False, help='Use more verbose output')
        parser.add_argument('-r', '--rev-range', dest='rev_range', default=None,
                            help='Specify a revision range; format is [start]:[end]')
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.history(**vars(args))

    def history(self, directory=None, rev_range=None, verbose=False, **kwargs):  # pragma: no cover
        """List changeset scripts in chronological order."""
        config = _get_config(directory)
        command.history(config, rev_range, verbose=verbose)


class AlembicHeadsSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('heads', help=self.heads.__doc__)
        parser.add_argument('--resolve-dependencies', dest='resolve_dependencies',
                            action='store_true', default=False,
                            help='Treat dependency versions as down revisions')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                            default=False, help='Use more verbose output')
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.heads(**vars(args))

    def heads(self, directory=None, verbose=False, resolve_dependencies=False,
              **kwargs):  # pragma: no cover
        """Show current available heads in the script directory"""
        config = _get_config(directory)
        command.heads(config, verbose=verbose,
                      resolve_dependencies=resolve_dependencies)


class AlembicBranchesSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('branches', help=self.branches.__doc__)
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                            default=False, help='Use more verbose output')
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.branches(**vars(args))

    def branches(self, directory=None, verbose=False, **kwargs):  # pragma: no cover
        """Show current branch points"""
        config = _get_config(directory)
        command.branches(config, verbose=verbose)


class AlembicCurrentSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('current', help=self.current.__doc__)
        parser.add_argument('--head-only', dest='head_only', action='store_true',
                            default=False,
                            help='Deprecated. Use --verbose for additional output')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                            default=False, help='Use more verbose output')
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.current(**vars(args))

    def current(self, directory=None, verbose=False, head_only=False, **kwargs):  # pragma: no cover
        """Display the current revision for each database."""
        config = _get_config(directory)
        command.current(config, verbose=verbose, head_only=head_only)


class AlembicStampSubcommand(AlembicSubcommand):
    def make_parser(self, subparsers):
        parser = subparsers.add_parser('stamp', help=self.stamp.__doc__)
        parser.add_argument('--tag', dest='tag', default=None,
                            help=("Arbitrary 'tag' name - can be used by custom "
                                  "env.py scripts"))
        parser.add_argument('--sql', dest='sql', action='store_true', default=False,
                            help=("Don't emit SQL to database - dump to standard "
                                  "output instead"))
        parser.add_argument('revision', default=None, help="revision identifier")
        parser.add_argument('-d', '--directory', dest='directory', default=None,
                            help=("migration script directory (default is "
                                  "'migrations')"))
        return parser

    def run(self, parser, args):
        self.stamp(**vars(args))

    def stamp(self, directory=None, revision='head', sql=False, tag=None,
              **kwargs):  # pragma: no cover
        """'stamp' the revision table with the given revision; don't run any
        migrations"""
        config = _get_config(directory)
        command.stamp(config, revision, sql=sql, tag=tag)
