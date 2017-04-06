import click
import os.path
import tempfile
from shipit_bot_uplift.sync import Bot


DEFAULT_CACHE = os.path.join(tempfile.gettempdir(), 'shipit_bot_cache')


@click.command()
@click.option('--secrets', required=True, help='Taskcluster Secrets path')
@click.option('--client-id', help='Taskcluster Client ID')
@click.option('--client-token', help='Taskcluster Client token')
@click.option('--cache-root', default=DEFAULT_CACHE, help='Cache for repository clones.')  # noqa
@click.argument('bugzilla_id', type=int, required=False)
def main(secrets, client_id, client_token, cache_root, bugzilla_id):
    """
    Run bot to sync bug & analysis on a remote server
    """
    bot = Bot(secrets, client_id, client_token)
    bot.use_cache(cache_root)
    if bugzilla_id:
        bot.run(only=[bugzilla_id, ])
    else:
        bot.run()


if __name__ == '__main__':
    main()
