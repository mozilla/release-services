# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from shipit_dashboard.models import BugResult, BugContributor, BugAnalysis


def serialize_contributor(contrib):
    """
    Helper to serialize a contributor
    """
    assert isinstance(contrib, BugContributor)
    return {
        'email': contrib.contributor.email,
        'name': contrib.contributor.name,
        'avatar': contrib.contributor.avatar_url,
        'roles': contrib.roles.split(','),
    }


def serialize_bug(bug):
    """
    Helper to serialize a bug from its payload
    """
    assert isinstance(bug, BugResult)

    payload = bug.payload_data
    if not payload:
        raise Exception('Missing payload')
    bug_data = payload.get('bug')
    analysis = payload.get('analysis')
    if not bug_data or not analysis:
        raise Exception('Missing Bug data or Analysis')

    # Build uplift
    uplift = None
    if analysis.get('uplift_comment'):
        comment = analysis['uplift_comment']
        if 'html' in comment:
            comment_html = comment['html'].replace('&', '&amp;')
        else:
            comment_html = comment.get('text', 'No comment.')
        uplift = {
            'id': comment['id'],
            'comment': comment_html,
        }

    # Build versions
    # TODO: check structure with sylvestre
    approval_base_flag = 'approval-mozilla-'
    versions = {}
    for a in bug_data.get('attachments', []):
        for flag in a['flags']:
            if not flag['name'].startswith(approval_base_flag):
                continue
            base_name = flag['name'].replace(approval_base_flag, '')
            name = '{} {}'.format(base_name, flag['status'])
            if name not in versions:
                versions[name] = {
                    'name': flag['name'],
                    'attachments': [],
                    'status': flag['status'],
                }
            versions[name]['attachments'].append(str(a['id']))

    # Build flags
    status_base_flag = 'cf_status_'
    tracking_base_flag = 'cf_tracking_'

    def _filter_flags(base):
        out = [(k.replace(base, '', 1), v) for k, v in bug_data.items() if k.startswith(base + 'firefox')]  # noqa
        return dict(out)

    return {
        # Base
        'id': bug.id,
        'bugzilla_id': bug.bugzilla_id,
        'url': payload.get('url', 'https://bugzil.la/{}'.format(bug.bugzilla_id)),  # noqa
        'summary': bug_data['summary'],
        'keywords': bug_data['keywords'],
        'flags_status': _filter_flags(status_base_flag),
        'flags_tracking': _filter_flags(tracking_base_flag),

        # Contributor
        'contributors': [serialize_contributor(c) for c in bug.contributors],

        # Stats
        'changes_size': analysis.get('changes_size', 0),

        # Uplift request
        'uplift': uplift,

        # Patches
        'patches': analysis['patches'],
        'landings': {k: v for k, v in analysis.get('landings', {}).items() if v is not None},  # noqa

        # Versions
        'versions': versions,
    }


def serialize_analysis(analysis, full=True):
    """
    Helper to serialize an analysis
    """
    assert isinstance(analysis, BugAnalysis)

    out = {
        'id': analysis.id,
        'name': analysis.name,
        'count': len(analysis.bugs),
        'parameters': analysis.parameters,
    }

    if full:
        # Add bugs
        out['bugs'] = [serialize_bug(b) for b in analysis.bugs if b.payload]
    else:
        out['bugs'] = []

    return out
