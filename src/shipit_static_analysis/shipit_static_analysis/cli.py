from shipit_static_analysis.workflow import Workflow
from cli_common.click import taskcluster_options
import click


@click.command()
@taskcluster_options
@click.argument('revisions', nargs=-1, envvar='REVISIONS')
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
def main(revisions, cache_root, *args, **kwargs):
    w = Workflow(cache_root)
    for rev in revisions:
        w.run(rev)


if __name__ == '__main__':
    main()
