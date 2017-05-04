from shipit_static_analysis.workflow import Workflow
import click


@click.command()
@click.argument('revisions', nargs=-1)
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(revisions, cache_root, secrets, client_id, client_token):
    w = Workflow(secrets, cache_root, client_id, client_token)
    for rev in revisions:
        w.run(revisions)


if __name__ == '__main__':
    main()
