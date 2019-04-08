# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

import click
import click_spinner

import cli_common.cli
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
    short_help='Run PROJECT in development mode.',
    epilog='Happy hacking!',
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
@click.option(
    '--interactive/--no-interactive',
    default=True,
    )
@cli_common.cli.taskcluster_options
@click.pass_context
def cmd(ctx,
        project,
        quiet,
        nix_shell,
        interactive,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
        ):

    project_config = please_cli.config.PROJECTS_CONFIG.get(project, {})
    run_type = project_config.get('run')
    run_options = project_config.get('run_options', {})

    if not run_type:
        raise click.ClickException(f'Application `{project}` is not configured to be runnable.')

    host = run_options.get('host', os.environ.get('HOST', '127.0.0.1'))
    port = str(run_options.get('port', 8000))
    schema = 'https://'
    project_name = project.replace('-', '_')
    ca_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'ca.crt')
    server_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.crt')
    server_key_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.key')

    os.environ['DEBUG'] = 'true'
    os.environ['PROJECT_NAME'] = project_name

    pg_host = please_cli.config.PROJECTS_CONFIG['postgresql']['run_options'].get('host', host)
    pg_port = str(please_cli.config.PROJECTS_CONFIG['postgresql']['run_options']['port'])

    redis_host = please_cli.config.PROJECTS_CONFIG['redis']['run_options'].get('host', host)
    redis_port = str(please_cli.config.PROJECTS_CONFIG['redis']['run_options']['port'])

    if 'postgresql' in project_config.get('requires', []):

        dbname = 'services'

        click.echo(f' => Checking if database `{dbname}` exists ... ', nl=False)
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

        if result != 0 and 'psql: could not connect to server' in output:
            click.secho('ERROR', fg='red')
            raise click.UsageError(
                'Could not connect to the database.\n\n'
                'Please run:\n\n'
                '    ./please run postgresql\n\n'
                'in a separate terminal.'
            )

        please_cli.utils.check_result(result, output, ask_for_details=interactive)

        database_exists = False
        for line in output.split('\n'):
            column1 = line.split('|')[0].strip()
            if column1 == dbname:
                database_exists = True
                break

        if not database_exists:
            click.echo(f' => Creating `{dbname}` database ` ... ', nl=False)
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
            please_cli.utils.check_result(result, output, ask_for_details=interactive)

        os.environ['DATABASE_URL'] = f'postgresql://{pg_host}:{pg_port}/{dbname}'

    if 'redis' in project_config.get('requires', []):

        # Check redis is running
        click.echo(' => Checking if redis is running... ', nl=False)
        with click_spinner.spinner():
            result, output, error = ctx.invoke(
                please_cli.shell.cmd,
                project=project,
                quiet=True,
                command=f'redis-cli -h {redis_host} -p {redis_port} ping',
                nix_shell=nix_shell,
                )

        please_cli.utils.check_result(result, output, ask_for_details=interactive)

        # Setup config for client application
        os.environ['REDIS_URL'] = f'redis://{redis_host}:{redis_port}'

    if run_type == 'POSTGRESQL':
        data_dir = run_options.get('data_dir', os.path.join(please_cli.config.TMP_DIR, 'postgresql'))

        if not os.path.isdir(data_dir):
            click.echo(f' => Initialize database folder `{data_dir}` ... ', nl=False)
            with click_spinner.spinner():
                result, output, error = ctx.invoke(please_cli.shell.cmd,
                                                   project=project,
                                                   command=f'initdb -D {data_dir} --auth=trust',
                                                   nix_shell=nix_shell,
                                                   )
            please_cli.utils.check_result(result, output, ask_for_details=interactive)

        schema = ''
        command = [
            'postgres',
            '-D', data_dir,
            '-h', host,
            '-p', port,
        ]

    elif run_type == 'REDIS':
        data_dir = run_options.get('data_dir', os.path.join(please_cli.config.TMP_DIR, 'redis'))
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        command = [
            'redis-server',
            '--dir', data_dir,
            '--bind', host,
            '--port', port,
        ]

    elif run_type == 'FLASK':

        for env_name, env_value in run_options.get('envs', {}).items():
            env_name = please_cli.utils.normalize_name(env_name).upper()
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
        os.environ['APP_URL'] = f'{schema}{host}:{port}'
        os.environ['CORS_ORIGINS'] = '*'

        command = [
            'gunicorn',
            please_cli.utils.normalize_name(project_name) + '.flask:app',
            '--bind', f'{host}:{port}',
            f'--ca-certs={ca_cert_file}',
            f'--certfile={server_cert_file}',
            f'--keyfile={server_key_file}',
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
        os.environ['HOST'] = host
        os.environ['PORT'] = port

        for env_name, env_value in run_options.get('envs', {}).items():
            env_name = 'WEBPACK_' + please_cli.utils.normalize_name(env_name).upper()
            os.environ[env_name] = env_value

        # XXX: once we move please_cli.config.PROJECTS to nix we wont need this
        for require in project_config.get('requires', []):
            env_name = 'WEBPACK_{}_URL'.format(please_cli.utils.normalize_name(require).upper())
            env_value = '{}://{}:{}'.format(
                please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('schema', 'https'),
                please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('host', host),
                please_cli.config.PROJECTS_CONFIG[require]['run_options']['port'],
            )
            os.environ[env_name] = env_value

        command = [
            'webpack-dev-server',
            '--host', host,
            '--port', port,
            '--config', os.path.join(please_cli.config.ROOT_DIR, 'src', project_name, 'webpack.config.js'),
        ]

    elif run_type == 'NEUTRINO':

        if not os.path.exists(ca_cert_file) or \
           not os.path.exists(server_cert_file) or \
           not os.path.exists(server_key_file):
            ctx.invoke(please_cli.create_certs.cmd,
                       certificates_dir=os.path.join(please_cli.config.TMP_DIR, 'certs'),
                       )

        envs = dict(
            SSL_CACERT=ca_cert_file,
            SSL_CERT=server_cert_file,
            SSL_KEY=server_key_file,
            HOST=host,
            PORT=port,
            RELEASE_VERSION=please_cli.config.VERSION,
            RELEASE_CHANNEL='development',
        )

        for require in project_config.get('requires', []):
            env_name = '{}_URL'.format(please_cli.utils.normalize_name(require).upper())
            env_value = '{}://{}:{}'.format(
                please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('schema', 'https'),
                please_cli.config.PROJECTS_CONFIG[require]['run_options'].get('host', host),
                please_cli.config.PROJECTS_CONFIG[require]['run_options']['port'],
            )
            envs[env_name] = env_value

        for env_name, env_value in run_options.get('envs', {}).items():
            env_name = please_cli.utils.normalize_name(env_name).upper()
            envs[env_name] = env_value

        for env_name, env_value in envs.items():
            os.environ[env_name] = env_value

        command = ['yarn', 'start']

    click.echo(f' => Running {project} on {schema}{host}:{port} ...')
    returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                           project=project,
                                           quiet=quiet,
                                           command=' '.join(command),
                                           nix_shell=nix_shell,
                                           taskcluster_secret=taskcluster_secret,
                                           taskcluster_client_id=taskcluster_client_id,
                                           taskcluster_access_token=taskcluster_access_token,
                                           )
    sys.exit(returncode)


if __name__ == '__main__':
    cmd()
