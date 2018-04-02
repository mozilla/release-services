# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import pprint
import click
import please_cli.config

HEROKU_COMMENT = "##Heroku {channel} app cnames##"
HEROKU_PRODUCTION = []
HEROKU_TESTING = []
HEROKU_STAGING = []
SHIPIT_PRODUCTION = []
SHIPIT_TESTING = []
SHIPIT_STAGING = []

HEADER = '''

######################################################################
#                                                                    #
# IMPORTANT: mozilla-releng.net resources were generated, do not     #
#            change them manually!                                   #
#                                                                    #
#     https://docs.mozilla-releng.net/deploy/configure-dns.html      #
#                                                                    #
######################################################################

resource "aws_route53_zone" "mozilla-releng" {
    name = "mozilla-releng.net."
}

# A special root alias that points to www.mozilla-releng.net
resource "aws_route53_record" "root-alias" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "mozilla-releng.net"
    type = "A"

    alias {
        name = "www.mozilla-releng.net"
        zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
        evaluate_target_health = false
    }
}

resource "aws_route53_record" "heroku-coalease-cname" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "coalesce.mozilla-releng.net"
    type = "CNAME"
    ttl = "180"
    records = ["oita-54541.herokussl.com"]
}
'''

HEROKU_TEMPLATE = '''
resource "aws_route53_record" "%(name)s" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "%(domain)s"
    type = "CNAME"
    ttl = "180"
    records = ["%(dns)s"]
}
'''
S3_TEMPLATE = '''
resource "aws_route53_record" "%(name)s" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "%(domain)s"
    type = "A"
    alias {
        name = "%(dns)s"
        zone_id = "Z2FDTNDATAQYW2"
        evaluate_target_health = false
    }
}
'''


def to_route53_name(project_id, channel):
    channel_short = ''
    if channel == 'production':
        channel_short = 'prod'
    elif channel == 'staging':
        channel_short = 'stage'
    elif channel == 'testing':
        channel_short = 'test'

    project_name = project_id
    if 'releng-' in project_id:
        project_name = project_name[7:]
    elif 'shipit-' in project_id:
        project_name = project_name[7:] + '-shipit'

    return 'heroku-%s-cname-%s' % (project_name,channel_short)


@click.command()
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    default=None,
    )
def cmd(channel):

    if channel is None:
        channels = please_cli.config.CHANNELS
    else:
        channels = [channel]

    click.echo(HEADER)

    for project_id in sorted(please_cli.config.PROJECTS_CONFIG.keys()):

        project = please_cli.config.PROJECTS_CONFIG[project_id].get('deploy_options')
        project_target = please_cli.config.PROJECTS_CONFIG[project_id].get('deploy')

        if project:

            for channel in sorted(channels):

                if channel not in project or \
                       'url' not in project[channel] or \
                       'dns' not in project[channel]:
                    continue

                if 'dns_url' in project[channel]:
                    domain = project[channel]['dns_url']
                else:
                    domain = project[channel]['url']
                    domain = domain.lstrip('https')
                    domain = domain.lstrip('http')
                    domain = domain.lstrip('://')

                def heroku(a, b):

                    if project_target == 'HEROKU' and a == channel and 'shipit-' not in project_id:
                        b.append(HEROKU_TEMPLATE % dict(
                            name=to_route53_name(project_id, channel),
                            domain=domain,
                            dns=project[channel]['dns'],
                         ))

                def shipit(a, b):

                    if project_target == 'HEROKU' and a == channel and 'shipit-' in project_id:
                        b.append(HEROKU_TEMPLATE % dict(
                            name=to_route53_name(project_id, channel),
                            domain=domain,
                            dns=project[channel]['dns'],
                         ))

                def comment(a):
                    line = '#' * len(HEROKU_COMMENT.format(channel=a))
                    click.echo(line)
                    click.echo(HEROKU_COMMENT.format(channel=a))
                    click.echo(line)

                heroku('production', HEROKU_PRODUCTION)
                heroku('testing', HEROKU_TESTING)
                heroku('staging', HEROKU_STAGING)

                shipit('production', SHIPIT_PRODUCTION)
                shipit('testing', SHIPIT_TESTING)
                shipit('staging', SHIPIT_STAGING)

                if project_target == 'S3':
                    click.echo(S3_TEMPLATE % dict(
                        name=to_route53_name(project_id, channel),
                        domain=domain,
                        dns=project[channel]['dns'],
                    ))

    comment('production')
    click.echo(pprint.pprint(HEROKU_PRODUCTION))

    comment('testing')
    click.echo(pprint.pprint(HEROKU_TESTING))

    comment('staging')
    click.echo(pprint.pprint(HEROKU_STAGING))

    comment('Shiptit production')
    click.echo(pprint.pprint(SHIPIT_PRODUCTION))

    comment('Shipit testing')
    click.echo(pprint.pprint(SHIPIT_TESTING))

    comment('Shipit staging')
    click.echo(pprint.pprint(SHIPIT_STAGING))



