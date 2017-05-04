import click
from shipit_pulse_listener.listener import PulseListener


@click.command()
@click.argument('branch', type=click.Choice(['staging', 'production']))
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(branch, secrets, client_id, client_token):
    pl = PulseListener(secrets, client_id, client_token)
    pl.run(branch)


if __name__ == '__main__':
    main()
