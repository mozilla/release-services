# -*- coding: utf-8 -*-

from cli_common.log import get_logger
from cli_common.taskcluster import get_service
from code_coverage_bot.phabricator import parse_revision_id
from code_coverage_bot.secrets import secrets

logger = get_logger(__name__)


def notify_email(revision, changesets, changesets_coverage, client_id, access_token):
    '''
    Send an email to admins when low coverage for new commits is detected
    '''
    notify_service = get_service('notify', client_id, access_token)

    content = ''
    for changeset in changesets:
        desc = changeset['desc'].split('\n')[0]

        if any(text in desc for text in ['r=merge', 'a=merge']):
            continue

        rev = changeset['node']

        # Lookup changeset coverage from phabricator uploader
        rev_id = parse_revision_id(changeset['desc'])
        if rev_id is None:
            continue
        coverage = changesets_coverage.get(rev_id)
        if coverage is None:
            logger.warn('No coverage found', changeset=changeset)
            continue

        # Calc totals for all files
        covered = sum(c['lines_covered'] for c in coverage.values())
        added = sum(c['lines_added'] for c in coverage.values())

        if covered < 0.2 * added:
            content += '* [{}](https://firefox-code-coverage.herokuapp.com/#/changeset/{}): {} covered out of {} added.\n'.format(desc, rev, covered, added)  # noqa

    if content == '':
        return
    elif len(content) > 102400:
        # Content is 102400 chars max
        content = content[:102000] + '\n\n... Content max limit reached!'

    for email in secrets[secrets.EMAIL_ADDRESSES]:
        notify_service.email({
            'address': email,
            'subject': 'Coverage patches for {}'.format(revision),
            'content': content,
            'template': 'fullscreen',
        })

    return content
