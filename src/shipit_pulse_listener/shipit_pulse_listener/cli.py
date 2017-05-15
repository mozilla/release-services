import click
from cli_common.click import taskcluster_options
from shipit_pulse_listener.listener import PulseListener


@click.command()
@taskcluster_options
@click.argument('branch', type=click.Choice(['staging', 'production']))
def main(branch, *args, **kwargs):
    pl = PulseListener()
    pl.run(branch)


if __name__ == '__main__':
    main()
