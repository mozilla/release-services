import click

from shipit_code_coverage.codecov import CodeCov


@click.command()
@click.option(
    '--cache-root',
    required=True,
    help='Cache root, used to pull changesets'
)
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(cache_root, secrets, client_id, client_token):
    c = CodeCov(cache_root, secrets, client_id, client_token)
    c.go()


if __name__ == '__main__':
    main()
