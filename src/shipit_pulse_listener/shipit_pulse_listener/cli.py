import click
from shipit_pulse_listener.listener import PulseListener


@click.command()
@click.argument('hooks', nargs=-1)
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(hooks, secrets, client_id, client_token):
    if not hooks:
        raise Exception('Specify at least one hook (hookGroupId:hookId)')

    pl = PulseListener(secrets, client_id, client_token)
    pl.run(hooks)


if __name__ == '__main__':
    main()
