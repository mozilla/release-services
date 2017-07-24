# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import sys

import click
import click_spinner

import please_cli.config
import please_cli.create_certs
import please_cli.shell
import please_cli.utils


CMD_HELP = '''
Run PROJECT in development mode.

\b
PROJECTS:
{projects}

'''.format(
    projects=''.join([' - ' + i + '\n' for i in please_cli.config.PROJECTS]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Run PROJECT in development mode.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.config.PROJECTS),
    )
@click.option(
    '-q', '--quiet',
    is_flag=True,
    help='Don\'t display output of a command.',
    )
@click.option(
    '--nix-shell',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-shell',
    help='`nix-shell` command',
    )
@click.pass_context
def cmd(ctx, project, quiet, nix_shell):

    project_config = please_cli.config.PROJECTS.get(project, {})
    run_type = project_config.get('run')
    run_options = project_config.get('run_options', {})

    if not run_type:
        raise click.ClickException('Application `{}` is not configured to be runnable.')

    host = run_options.get('host', 'localhost')
    if please_cli.config.IN_DOCKER:
        host = run_options.get('host', '0.0.0.0')
    port = str(run_options.get('port', 8000))
    schema = 'https://'
    project_name = project.replace('-', '_')
    ca_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'ca.crt')
    server_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.crt')
    server_key_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.key')

    os.environ['DEBUG'] = 'true'
    os.environ['PROJECT_NAME'] = project_name

    pg_host = please_cli.config.PROJECTS['postgresql']['run_options'].get('host', host)
    pg_port = str(please_cli.config.PROJECTS['postgresql']['run_options']['port'])

    if 'postgresql' in project_config.get('requires', []):

        dbname = 'services'

        click.echo(' => Checking if database `{}` exists ... '.format(dbname), nl=False)
        with click_spinner.spinner():
            result, output, error = ctx.invoke(
                please_cli.shell.cmd,
                project=project,
                quiet=True,
                command=' '.join([
                    'psql',
                    '-lqt',
                    '-h', pg_host,
                    '-p', pg_port,
                ]),
                nix_shell=nix_shell,
                )

        database_exists = False
        for line in output.split('\n'):
            column1 = line.split('|')[0].strip()
            if column1 == dbname:
                database_exists = True
                break

        if result != 0:
            click.secho('ERROR', fg='red')
            raise click.UsageError(
                'Could not connect to the database.\n\n'
                'Please run:\n\n'
                '    ./please run postgresql\n\n'
                'in a separate terminal.'
            )

        please_cli.utils.check_result(result, output)

        if not database_exists:
            click.echo(' => Creating `{}` database ` ... '.format(dbname), nl=False)
            with click_spinner.spinner():
                result, output, error = ctx.invoke(
                    please_cli.shell.cmd,
                    project=project,
                    command=' '.join([
                        'createdb',
                        '-h', pg_host,
                        '-p', pg_port,
                        dbname,
                    ]),
                    nix_shell=nix_shell,
                    )
            please_cli.utils.check_result(result, output)

        os.environ['DATABASE_URL'] = 'postgresql://{}:{}/{}'.format(
            pg_host, pg_port, dbname
        )

    if run_type == 'POSTGRESQL':
        data_dir = run_options.get('data_dir', os.path.join(please_cli.config.TMP_DIR, 'postgresql'))

        if not os.path.isdir(data_dir):
            click.echo(' => Initialize database folder `{}` ... '.format(data_dir), nl=False)
            with click_spinner.spinner():
                result, output, error = ctx.invoke(please_cli.shell.cmd,
                                                   project=project,
                                                   command='initdb -D {} --auth=trust'.format(data_dir),
                                                   nix_shell=nix_shell,
                                                   )
            please_cli.utils.check_result(result, output)

        schema = ''
        command = [
            'postgres',
            '-D', data_dir,
            '-h', host,
            '-p', port,
        ]

    elif run_type == 'FLASK':

        for env_name, env_value in run_options.get('envs', {}).items():
            env_name = env_name.replace('-', '_').upper()
            os.environ[env_name] = env_value

        if not os.path.exists(ca_cert_file) or \
           not os.path.exists(server_cert_file) or \
           not os.path.exists(server_key_file):
            ctx.invoke(please_cli.create_certs.cmd,
                       certificates_dir=os.path.join(please_cli.config.TMP_DIR, 'certs'),
                       )

        project_cache_dir = os.path.join(please_cli.config.TMP_DIR, 'cache', project_name)
        if not os.path.isdir(project_cache_dir):
            os.makedirs(project_cache_dir)

        os.environ['CACHE_TYPE'] = 'filesystem'
        os.environ['CACHE_DIR'] = project_cache_dir
        os.environ['APP_SETTINGS'] = os.path.join(
            please_cli.config.ROOT_DIR, 'src', project_name, 'settings.py')
        os.environ['APP_URL'] = '{}{}:{}'.format(schema, host, port)
        os.environ['CORS_ORIGINS'] = '*'

        command = [
            'gunicorn',
            project_name + '.flask:app',
            '--bind', '{}:{}'.format(host, port),
            '--ca-certs={}'.format(ca_cert_file),
            '--certfile={}'.format(server_cert_file),
            '--keyfile={}'.format(server_key_file),
            '--workers', '2',
            '--timeout', '3600',
            '--reload',
            '--reload-engine=poll',
            '--log-file', '-',
        ]

    elif run_type == 'SPHINX':

        schema = 'http://'
        command = [
            'HOST=' + host,
            'PORT=' + port,
            'python', 'run.py',
        ]

    elif run_type == 'ELM':

        if not os.path.exists(ca_cert_file) or \
           not os.path.exists(server_cert_file) or \
           not os.path.exists(server_key_file):
            ctx.invoke(please_cli.create_certs.cmd,
                       certificates_dir=os.path.join(please_cli.config.TMP_DIR, 'certs'),
                       )

        os.environ['WEBPACK_RELEASE_VERSION'] = please_cli.config.VERSION
        os.environ['WEBPACK_RELEASE_CHANNEL'] = 'development'
        os.environ['SSL_CACERT'] = ca_cert_file
        os.environ['SSL_CERT'] = server_cert_file
        os.environ['SSL_KEY'] = server_key_file

        for env_name, env_value in run_options.get('envs', {}).items():
            env_name = 'WEBPACK_' + env_name.replace('-', '_').upper()
            os.environ[env_name] = env_value

        # XXX: once we move please_cli.config.PROJECTS to nix we wont need this
        for require in project_config.get('requires', []):
            env_name = 'WEBPACK_{}_URL'.format(require.replace('-', '_').upper())
            env_value = '{}://{}:{}'.format(
                please_cli.config.PROJECTS[require]['run_options'].get('schema', 'https'),
                please_cli.config.PROJECTS[require]['run_options'].get('host', host),
                please_cli.config.PROJECTS[require]['run_options']['port'],
            )
            os.environ[env_name] = env_value

        command = [
            'webpack-dev-server',
            '--host', host,
            '--port', port,
            '--config', os.path.join(please_cli.config.ROOT_DIR, 'src', project_name, 'webpack.config.js'),
        ]

    click.echo(' => Running {} on {}{}:{} ...'.format(project, schema, host, port))
    returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                           project=project,
                                           quiet=quiet,
                                           command=' '.join(command),
                                           nix_shell=nix_shell,
                                           )
    sys.exit(returncode)


if __name__ == "__main__":
    cmd()
