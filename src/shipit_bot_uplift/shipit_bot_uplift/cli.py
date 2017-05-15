import click
import os.path
import tempfile
from shipit_bot_uplift.sync import Bot
from cli_common.click import taskcluster_options


DEFAULT_CACHE = os.path.join(tempfile.gettempdir(), 'shipit_bot_cache')


@click.command()
@taskcluster_options
@click.option('--cache-root', default=DEFAULT_CACHE, help='Cache for repository clones.')  # noqa
@click.argument('bugzilla_id', type=int, required=False)
def main(taskcluster_client_id, taskcluster_access_token, cache_root, bugzilla_id, *args, **kwargs):  # noqa
    """
    Run bot to sync bug & analysis on a remote server
    """
    bot = Bot(taskcluster_client_id, taskcluster_access_token)
    bot.use_cache(cache_root)
    if bugzilla_id:
        bot.run(only=[bugzilla_id, ])
    else:
        bot.run()


if __name__ == '__main__':
    main()
