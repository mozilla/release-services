#!/usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python3.pkgs.requests python3.pkgs.click

import json
import click

import requests


@click.command()
@click.option('--username', prompt='LDAP username')
@click.option('--password', prompt='LDAP password', hide_input=True)
@click.option('--api-from', default='https://ship-it.mozilla.org')
@click.option('--api-to', required=True)
def main(username, password, api_from, api_to):

    s = requests.Session()
    s.auth = (username, password)

    click.echo('Fetching release list...', nl=False)
    req = s.get(f'{api_from}/releases')
    releases = req.json()['releases']
    click.echo(click.style('OK', fg='green'))

    releases_json = []

    with click.progressbar(releases, label='Fetching release data') as releases:
        for release in releases:
            r = s.get(f'{api_from}/releases/{release}')
            releases_json.append(r.json())

    click.echo('Syncing release list...', nl=False)
    r = requests.post(f'{api_to}/sync', verify=False, json=releases_json)
    r.raise_for_status()
    click.echo(click.style('OK', fg='green'))



if __name__ == '__main__':
    main()
