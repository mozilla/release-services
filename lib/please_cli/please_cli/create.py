# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import click
import cookiecutter.main

import please_cli.config
import please_cli.utils

CMD_HELP = '''
Create a new PROJECT from a TEMPLATE

\b
TEMPLATES:
{templates}
'''.format(
    templates=''.join([' - ' + i + '\n' for i in please_cli.config.TEMPLATES]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help='Create PROJECT initial structure.',
    epilog='Happy hacking!',
    help=CMD_HELP,
    )
@click.argument(
    'template',
    required=True,
    type=click.Choice(please_cli.config.TEMPLATES),
    )
@click.argument(
    'project',
    required=True,
    type=str,
    )
@click.pass_context
def cmd(ctx, template, project):
    '''
    '''

    template_dir = os.path.join(please_cli.config.ROOT_DIR, 'nix', 'templates', template)
    if not os.path.isdir(template_dir):
        raise

    project_dir = os.path.join(please_cli.config.SRC_DIR, project)
    if os.path.isdir(project_dir):
        raise

    template_options = dict(project=project)
    template_options['project_path'] = project.replace('-', '_')
    template_options['project_url'] = 'TODO'
    if project.startswith('releng-'):
        template_options['project_url'] = f"{project[len('releng-'):]}.mozilla-releng.net"

    click.echo('=> Creating project structure ...')
    cookiecutter.main.cookiecutter(
        template_dir,
        no_input=True,
        extra_context=template_options,
        output_dir=please_cli.config.SRC_DIR,
    )

    click.secho(f'\nProject `{project}` created sucessfully!', fg='green', bold=True)
    click.echo('\nCode is located at:')
    click.echo(f'    src/{project}')
    click.echo('\nTo enter development environemnt run:')
    click.echo(f'    ./please shell {project}')
    click.echo(f'\nTo read more about `{template}` template visit:')
    click.echo(f'    https://docs.mozilla-releng.net/develop/template-{template}.html')
    click.echo('')
