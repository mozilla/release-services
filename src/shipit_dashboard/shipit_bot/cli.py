import argparse
from shipit_bot.sync import BotRemote


def main():
    """
    Run bot to sync bug & analysis on a remote server
    """
    parser = argparse.ArgumentParser(description='Sync bug & analysis')
    parser.add_argument(
        '--secrets',
        type=str,
        dest='secrets',
        default='project/shipit/bot/staging',
        help='Taskcluster Secrets path')
    parser.add_argument(
        '--client-id',
        type=str,
        dest='client_id',
        help='Taskcluster Client ID')
    parser.add_argument(
        '--client-token',
        type=str,
        dest='client_token',
        help='Taskcluster Client token')
    args = parser.parse_args()

    bot = BotRemote(args.secrets, args.client_id, args.client_token)
    bot.run()


if __name__ == '__main__':
    main()
