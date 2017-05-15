import click
from shipit_risk_assessment.bot import Bot


@click.command()
@click.argument('work_dir')
@click.argument('merge_revision', envvar='REVISION')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
def main(work_dir, merge_revision, client_id, client_token):
    bot = Bot(client_id, client_token)
    bot.run(work_dir, merge_revision)


if __name__ == '__main__':
    main()
