from shipit_static_analysis.workflow import Workflow
import click


@click.command()
@click.option(
    '--revision',
    required=True,
    help='Mercurial revision to use for static analysis'
)
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(revision, cache_root, secrets, client_id, client_token):
    w = Workflow(secrets, cache_root, client_id, client_token)
    w.run(revision)


if __name__ == '__main__':
    main()
