import click
from cli_common.click import taskcluster_options
from shipit_pulse_listener.listener import PulseListener


@click.command()
@taskcluster_options
def main(*args, **kwargs):
    pl = PulseListener()
    pl.run()


if __name__ == '__main__':
    main()
