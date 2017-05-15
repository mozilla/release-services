import click
from cli_common.click import taskcluster_options
from shipit_risk_assessment.bot import Bot


@click.command()
@taskcluster_options
@click.argument('work_dir')
@click.argument('merge_revision', envvar='REVISION')
def main(work_dir, merge_revision, *args, **kwargs):
    bot = Bot()
    bot.run(work_dir, merge_revision)


if __name__ == '__main__':
    main()
