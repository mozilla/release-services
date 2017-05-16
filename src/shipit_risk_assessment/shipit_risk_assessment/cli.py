import click
from cli_common.click import taskcluster_options
from shipit_risk_assessment.bot import Bot


@click.command()
@taskcluster_options
@click.argument('work_dir')
@click.argument('revisions', envvar='REVISIONS')
def main(work_dir, revisions, *args, **kwargs):
    bot = Bot(work_dir)
    for revision in revisions.split(' '):
        bot.run(revision)


if __name__ == '__main__':
    main()
