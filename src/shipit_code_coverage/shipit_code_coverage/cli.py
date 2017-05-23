import click
from cli_common.click import taskcluster_options
from shipit_code_coverage.codecov import CodeCov


@click.command()
@taskcluster_options
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
def main(cache_root, *args, **kwargs):
    c = CodeCov(cache_root)
    c.go()


if __name__ == '__main__':
    main()
