# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import subprocess

import cli_common.command
import click
import click_spinner
import please_cli.config
import please_cli.utils


@click.command()
@click.option(
    '--certificates-dir',
    required=True,
    default=os.path.join(please_cli.config.TMP_DIR, 'certs'),
    help='Directory where to create certificated',
    )
@click.option(
    '--openssl',
    required=True,
    default=please_cli.config.OPENSSL_BIN_DIR + 'openssl',
    help='Path to openssl command (default: {}).'.format(
        please_cli.config.OPENSSL_BIN_DIR + 'openssl',
        ),
    )
@click.option(
    '--c-rehash',
    required=True,
    default=please_cli.config.OPENSSL_BIN_DIR + 'c_rehash',
    help='Path to c_rehash command (default: {}).'.format(
        please_cli.config.OPENSSL_BIN_DIR + 'c_rehash',
        ),
    )
@click.option(
    '--openssl-config',
    required=True,
    default=please_cli.config.OPENSSL_ETC_DIR + 'openssl.cnf',
    help='Path to openssl configuration (default: {}).'.format(
        please_cli.config.OPENSSL_ETC_DIR + 'openssl.cnf',
        ),
    )
def cmd(certificates_dir, openssl, c_rehash, openssl_config, interactive=True):

    if not os.path.isdir(certificates_dir):
        click.echo(' => Creating certificates directory ... ')
        with click_spinner.spinner():
            os.makedirs(certificates_dir)
        please_cli.utils.check_result(0, '', ask_for_details=interactive)

    ca_key_file = os.path.join(certificates_dir, 'ca.key')
    ca_cert_file = os.path.join(certificates_dir, 'ca.crt')

    if os.path.exists(ca_key_file) or os.path.exists(ca_cert_file):
        click.echo(' => Removing existing certificates ... ')
        with click_spinner.spinner():
            if os.path.exists(ca_key_file):
                os.unlink(ca_key_file)
            if os.path.exists(ca_cert_file):
                os.unlink(ca_cert_file)
        please_cli.utils.check_result(0, '', ask_for_details=interactive)

    click.echo(' => Building CA certificate key ... ', nl=False)
    with click_spinner.spinner():
        result, output, error = cli_common.command.run(
            [
                openssl,
                'genrsa',
                '-out', ca_key_file,
                '2048',
            ],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)

    click.echo(' => Self signing CA certificate  ... ', nl=False)
    with click_spinner.spinner():
        result, output, error = cli_common.command.run(
            [
                openssl,
                'req', '-x509', '-new', '-nodes',
                '-key', ca_key_file,
                '-days', '1024',
                '-out', ca_cert_file,
                '-subj', '/C=FR/ST=France/L=Paris/O=Mozilla/OU=Dev/CN=RelEngServices',
            ],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)

    server_key_file = os.path.join(certificates_dir, 'server.key')
    server_cert_file = os.path.join(certificates_dir, 'server.crt')
    server_csr_file = os.path.join(certificates_dir, 'server.csr')
    server_cnf_file = os.path.join(certificates_dir, 'server.cnf')

    if os.path.exists(server_key_file):
        os.unlink(server_key_file)

    if os.path.exists(server_cert_file):
        os.unlink(server_cert_file)

    if os.path.exists(server_csr_file):
        os.unlink(server_csr_file)

    if os.path.exists(server_cnf_file):
        os.unlink(server_cnf_file)

    click.echo(' => Building backend private certificate key ... ', nl=False)
    with click_spinner.spinner():
        result, output, error = cli_common.command.run(
            [
                openssl,
                'genrsa',
                '-out', server_key_file,
                '2048',
            ],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)

    click.echo(' => Creating openssh configuration ... ', nl=False)
    with open(openssl_config, 'r') as f:
        openssl_config_content = f.read()
    with open(server_cnf_file, 'w+') as f:
        f.write('{}\n[SAN]\nsubjectAltName=DNS:localhost,DNS:127.0.0.1'.format(openssl_config_content))
    please_cli.utils.check_result(0, '', ask_for_details=interactive)

    click.echo(' => Building backend csr certificate with mandatory subjectAltName ... ', nl=False)
    with click_spinner.spinner():
        result, output, error = cli_common.command.run(
            [
                openssl,
                'req', '-sha256', '-new',
                '-key', server_key_file,
                '-out', server_csr_file,
                '-subj', '/C=FR/ST=France/L=Paris/O=Mozilla/OU=Dev/CN=localhost',
                '-reqexts', 'SAN',
                '-config', server_cnf_file,
            ],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)

    click.echo(' => Signing server certificate with CA certificate ... ', nl=False)
    with click_spinner.spinner():
        result, output, error = cli_common.command.run(
            [
                openssl,
                'x509', '-req',
                '-in', server_csr_file,
                '-CA', ca_cert_file,
                '-CAkey', ca_key_file,
                '-CAcreateserial',
                '-out', server_cert_file,
                '-days', '500',
                '-extensions', 'SAN',
                '-extfile', server_cnf_file,
            ],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)

    click.echo(' => Hash certificates directory ... ', nl=False)
    with click_spinner.spinner():
        os.unlink(server_csr_file)
        result, output, error = cli_common.command.run(
            [c_rehash, certificates_dir],
            stream=True,
            stderr=subprocess.STDOUT,
        )
    please_cli.utils.check_result(result, output, ask_for_details=interactive)


if __name__ == "__main__":
    cmd()
