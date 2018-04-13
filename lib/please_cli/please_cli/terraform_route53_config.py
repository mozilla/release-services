# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
import click
import please_cli.config

HEROKU_COMMENT = '## Heroku {channel} app cnames ##'

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
HEROKU_TEMPLATE_EXTRA_PRODUCTION = '''
resource "aws_route53_record" "heroku-coalease-cname" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "coalesce.mozilla-releng.net"
    type = "CNAME"
    ttl = "180"
    records = ["oita-54541.herokussl.com"]
}
'''

S3_TEMPLATE = '''
############################
## CloudFront CDN aliases ##
############################

variable "cloudfront_alias" {
    default = [%(aliases)s]
}

# Cloudfront Alias Targets
# In the future, these may be sourced directly from terraform cloudfront resources
# should we decide to manage cloudfronts in terraform
variable "cloudfront_alias_domain" {
    type = "map"
    default = {%(alias_targets)s}
}

# A (Alias) records for cloudfront apps
resource "aws_route53_record" "cloudfront-alias" {
    zone_id = "${aws_route53_zone.mozilla-releng.zone_id}"
    name = "${element(var.cloudfront_alias, count.index)}.mozilla-releng.net"
    type = "A"
    count = "${length(var.cloudfront_alias)}"

    alias {
        name = "${var.cloudfront_alias_domain[element(var.cloudfront_alias, count.index)]}.cloudfront.net."
        zone_id = "Z2FDTNDATAQYW2"
        evaluate_target_health = false
    }
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
'''


def echo_heroku_comment(channel):
    line = '#' * len(HEROKU_COMMENT.format(channel=channel))
    click.echo(line)
    click.echo(HEROKU_COMMENT.format(channel=channel))
    click.echo(line)


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
def cmd():
    HEROKU_RELENG = dict()
    HEROKU_SHIPIT = dict()
    S3 = []

    for (project_id, project) in please_cli.config.PROJECTS_CONFIG.items():

        project_deploy_options = project.get('deploy_options')

        if project_deploy_options:

            for channel in project_deploy_options.keys():

                if channel not in project_deploy_options or \
                       'url' not in project_deploy_options[channel] or \
                       'dns' not in project_deploy_options[channel]:
                    continue

                if 'dns_url' in project_deploy_options[channel]:
                    domain = project_deploy_options[channel]['dns_url']
                else:
                    domain = project_deploy_options[channel]['url']
                    domain = domain.lstrip('https')
                    domain = domain.lstrip('http')
                    domain = domain.lstrip('://')


                if project.get('deploy') == 'HEROKU':
                    if project_id.startswith('releng-'):
                        HEROKU_RELENG.setdefault(channel, [])
                        HEROKU_RELENG[channel].append(dict(
                            name=to_route53_name(project_id, channel),
                            domain=domain,
                            dns=project_deploy_options[channel]['dns'],
                        ))
                    if project_id.startswith('shipit-'):
                        HEROKU_SHIPIT.setdefault(channel, [])
                        HEROKU_SHIPIT[channel].append(dict(
                            name=to_route53_name(project_id, channel),
                            domain=domain,
                            dns=project_deploy_options[channel]['dns'],
                        ))

                if project.get('deploy') == 'S3':
                    if project_id == 'releng-frontend':
                        if channel == 'production':
                            alias = 'www'
                        else:
                            alias = channel
                    elif project_id == 'shipit-frontend':
                        if channel == 'production':
                            alias = 'shipit'
                        else:
                            alias = 'shipit.' + channel
                    else:
                        alias = project_id.lstrip('releng-').lstrip('shipit-')
                        alias = '{}.{}'.format(alias, channel)
                        if channel == 'production':
                            alias = alias.rstrip('.production')

                    alias_target = project_deploy_options[channel].get('dns', '')
                    alias_target = alias_target.rstrip('.cloudfront.net.')
                    S3.append((alias, alias_target))


    click.echo(HEADER)

    channels = ['production', 'staging', 'testing']

    for channel in channels:
        projects = HEROKU_RELENG.get(channel, [])
        if projects:
            echo_heroku_comment(channel)
            if channel == 'production':
                click.echo(HEROKU_TEMPLATE_EXTRA_PRODUCTION)
            for project in sorted(projects, key=lambda x: x['name']):
                click.echo(HEROKU_TEMPLATE % project)

    for channel in channels:
        projects = HEROKU_SHIPIT.get(channel, [])
        if projects:
            echo_heroku_comment('shipit ' + channel)
            for project in sorted(projects, key=lambda x: x['name']):
                click.echo(HEROKU_TEMPLATE % project)


    aliases = ('\n' + ' ' * 8)
    aliases += ('\n' + ' ' * 8).join(['"{}",'.format(alias) for (alias, alias_target) in S3])
    aliases += ('\n' + ' ' * 4)

    alias_targets = ('\n' + ' ' * 8)
    alias_targets += ('\n' + ' ' * 8).join(['{} = "{}",'.format(alias, alias_target) for (alias, alias_target) in S3])
    alias_targets += ('\n' + ' ' * 4)

    click.echo(S3_TEMPLATE % dict(
        aliases=aliases,
        alias_targets=alias_targets,
    ))
