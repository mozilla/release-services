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
Run APPLICATION in development mode.

\b
APPLICATIONS:
{apps}

'''.format(
    apps=''.join([' - ' + i + '\n' for i in please_cli.config.APPS]),
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Run APPLICATION in development mode.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'app',
    required=True,
    type=click.Choice(please_cli.config.APPS),
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
def cmd(ctx, app, quiet, nix_shell):

    app_config = please_cli.config.APPS.get(app, {})
    run_type = app_config.get('run')
    run_options = app_config.get('run_options', {})

    if not run_type:
        raise click.ClickException('Application `{}` is not configured to be runnable.')

    host = run_options.get('host', 'localhost')  # TODO: needs to be 0.0.0.0 when inside docker
    port = str(run_options.get('port', 8000))
    schema = 'https://'
    app_name = app.replace('-', '_')
    ca_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'ca.crt')
    server_cert_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.crt')
    server_key_file = os.path.join(please_cli.config.TMP_DIR, 'certs', 'server.key')

    os.environ['DEBUG'] = 'true'

    pg_host = please_cli.config.APPS['postgresql']['run_options'].get('host', host)
    pg_port = str(please_cli.config.APPS['postgresql']['run_options']['port'])

    if 'postgresql' in app_config.get('requires', []):

        dbname = 'services'

        click.echo(' => Checking if database `{}` exists ... '.format(dbname), nl=False)
        with click_spinner.spinner():
            result, output, error = ctx.invoke(
                please_cli.shell.cmd,
                app=app,
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
            raise click.UserError(
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
                    app=app,
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
                                                   app=app,
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

        if not os.path.exists(ca_cert_file) or \
           not os.path.exists(server_cert_file) or \
           not os.path.exists(server_key_file):
            ctx.invoke(please_cli.create_certs.cmd,
                       certificates_dir=os.path.join(please_cli.config.TMP_DIR, 'certs'),
                       )

        app_cache_dir = os.path.join(please_cli.config.TMP_DIR, 'cache', app_name)
        if not os.path.isdir(app_cache_dir):
            os.makedirs(app_cache_dir)

        os.environ['CACHE_TYPE'] = 'filesystem'
        os.environ['CACHE_DIR'] = app_cache_dir
        os.environ['APP_SETTINGS'] = os.path.join(
            please_cli.config.ROOT_DIR, 'src', app_name, 'settings.py')
        os.environ['APP_URL'] = '{}{}:{}'.format(schema, host, port)
        os.environ['CORS_ORIGINS'] = '*'

        command = [
            'gunicorn',
            app_name + '.flask:app',
            '--bind', '{}:{}'.format(host, port),
            '--ca-certs={}'.format(ca_cert_file),
            '--certfile={}'.format(server_cert_file),
            '--keyfile={}'.format(server_key_file),
            '--workers', '1',
            '--timeout', '3600',
            '--reload',
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

        os.environ['WEBPACK_VERSION'] = 'v{} (devel)'.format(please_cli.config.VERSION)
        os.environ['SSL_CACERT'] = ca_cert_file
        os.environ['SSL_CERT'] = server_cert_file
        os.environ['SSL_KEY'] = server_key_file

        for require in app_config.get('requires', []):
            env_name = 'WEBPACK_{}_URL'.format(('-'.join(require.split('-')[1:])).upper())
            env_value = '{}://{}:{}'.format(
                please_cli.config.APPS[require]['run_options'].get('schema', 'https'),
                please_cli.config.APPS[require]['run_options'].get('host', host),
                please_cli.config.APPS[require]['run_options']['port'],
            )
            os.environ[env_name] = env_value

        for env_name, env_value in run_options.get('envs', []):
            os.environ[env_name] = env_value

        command = [
            'webpack-dev-server',
            '--host', host,
            '--port', port,
            '--config', os.path.join(please_cli.config.ROOT_DIR, 'src', app_name, 'webpack.config.js'),
        ]

    click.echo(' => Running {} on {}{}:{} ...'.format(app, schema, host, port))
    returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                           app=app,
                                           quiet=quiet,
                                           command=' '.join(command),
                                           nix_shell=nix_shell,
                                           )
    sys.exit(returncode)


if __name__ == "__main__":
    cmd()
