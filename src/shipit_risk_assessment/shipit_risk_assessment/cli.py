# -*- coding: utf-8 -*-
import click
from cli_common.click import taskcluster_options
from cli_common.log import init_logger
from cli_common.taskcluster import get_secrets
from shipit_risk_assessment.bot import Bot
from shipit_risk_assessment import config


@click.command()
@taskcluster_options
@click.argument('work_dir')
@click.argument('revisions', envvar='REVISIONS')
def main(work_dir,
         revisions,
         taskcluster_secret,
         taskcluster_client_id,
         taskcluster_access_token,
         ):

    secrets = get_secrets(taskcluster_secret,
                          config.PROJECT_NAME,
                          taskcluster_client_id=taskcluster_client_id,
                          taskcluster_access_token=taskcluster_access_token,
                          )

    init_logger(config.PROJECT_NAME,
                PAPERTRAIL_HOST=secrets.get('PAPERTRAIL_HOST'),
                PAPERTRAIL_PORT=secrets.get('PAPERTRAIL_PORT'),
                SENTRY_DSN=secrets.get('SENTRY_DSN'),
                MOZDEF=secrets.get('MOZDEF'),
                )

    bot = Bot(work_dir)
    for revision in revisions.split(' '):
        bot.run(revision)


if __name__ == '__main__':
    main()
