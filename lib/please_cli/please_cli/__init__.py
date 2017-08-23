# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import logbook
import cli_common.log

import please_cli.base_image
import please_cli.build
import please_cli.check
import please_cli.check_cache
import please_cli.create_certs
import please_cli.decision_task
import please_cli.deploy
import please_cli.maintanance
import please_cli.nagios_config
import please_cli.nixify
import please_cli.run
import please_cli.shell
import please_cli.terraform_route53_config
import please_cli.update_dependencies
import please_cli.utils


CMD_HELP = '''

Welcome to `please` command line utility which should help you develop
`mozilla-releng/services` projects.

To enter a development shell of project do:

  % ./please shell <PROJECT>

To run project in a foreground mode do:

  % ./please run <PROJECT>

To run tests, linters, etc... do:

  % ./please check <PROJECT>

Above is usefull to run before pushing code to upstream repository.

\b
PROJECTS:
{projects}

'''.format(
    projects=''.join([' - ' + i + '\n' for i in please_cli.config.PROJECTS]),
)

CMD_EPILOG = '''
For tools information look at:

  https://docs.mozilla-releng.net

Happy hacking!
'''.format(
)


@click.group("please", cls=please_cli.utils.ClickCustomGroup,
             invoke_without_command=True, help=CMD_HELP, epilog=CMD_EPILOG)
@click.option('-v', '--verbose', count=True, help='Increase verbosity level')
@click.version_option(version=please_cli.config.VERSION)
@click.help_option()
@click.pass_context
def cmd(ctx, verbose):

    # we start with warning level
    log_level = logbook.WARNING

    # log_level=1 is info – for messages you usually don’t want to see
    if verbose == 1:
        log_level = logbook.INFO

    # log_level>1 is debug – for debug messages
    elif verbose > 1:
        log_level = logbook.DEBUG

    cli_common.log.init_logger('please-cli', level=log_level)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cmd.add_command(please_cli.check.cmd, "check")
cmd.add_command(please_cli.run.cmd, "run")
cmd.add_command(please_cli.shell.cmd, "shell")


@click.group()
@click.pass_context
def cmd_tools(ctx):
    """Different tools and helping utilities.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cmd.add_command(cmd_tools, "tools")
cmd_tools.add_command(please_cli.base_image.cmd, "base-image")
cmd_tools.add_command(please_cli.build.cmd, "build")
cmd_tools.add_command(please_cli.check_cache.cmd, "check-cache")
cmd_tools.add_command(please_cli.create_certs.cmd, "create-certs")
cmd_tools.add_command(please_cli.decision_task.cmd, "decision-task")
cmd_tools.add_command(please_cli.deploy.cmd_HEROKU, "deploy:HEROKU")
cmd_tools.add_command(please_cli.deploy.cmd_S3, "deploy:S3")
cmd_tools.add_command(please_cli.deploy.cmd_TASKCLUSTER_HOOK, "deploy:TASKCLUSTER_HOOK")
cmd_tools.add_command(please_cli.maintanance.cmd_off, "maintanance:off")
cmd_tools.add_command(please_cli.maintanance.cmd_on, "maintanance:on")
cmd_tools.add_command(please_cli.nagios_config.cmd, "nagios-config")
cmd_tools.add_command(please_cli.nixify.cmd, "nixify")
cmd_tools.add_command(please_cli.terraform_route53_config.cmd, "terraform-route53-config")
cmd_tools.add_command(please_cli.update_dependencies.cmd, "update-dependencies")


if __name__ == "__main__":
    cmd()
