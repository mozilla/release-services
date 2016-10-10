import hashlib


def serialize_user(user):
    """
    Helper to serialize a user
    and adding a gravatar url
    """
    if isinstance(user, dict):
        out = user
        if 'email' not in out:
            out['email'] = out['name'] # weird case of uplift authors
    else:
        out = {
            'email' : user,
            'real_name' : user,
        }

    # Add gravatar
    email = out['email'].strip().lower()
    h = hashlib.md5(email.encode('utf-8'))
    out['avatar'] = 'https://www.gravatar.com/avatar/{}'.format(h.hexdigest())

    return out

def serialize_bug(bug):
    """
    Helper to serialize a bug from its payload
    """
    payload = bug.payload_data
    if not payload:
        raise Exception('Missing payload')
    bug_data = payload.get('bug')
    analysis = payload.get('analysis')
    if not bug_data or not analysis:
        raise Exception('Missing Bug data or Analysis')

    # Build uplift
    uplift = None
    if analysis.get('uplift_comment') and analysis.get('uplift_author'):
        author = analysis['uplift_author']
        comment = analysis['uplift_comment']
        uplift = {
            'id' : comment['id'],
            'author' : serialize_user(author),
            'comment' : comment['text'],
        }

    status_base_flag = 'cf_status_'
    tracking_base_flag = 'cf_tracking_'

    def _filter_flags(base):
        out = [(k.replace(base, '', 1), v) for k,v in bug_data.items() if k.startswith(base + 'firefox')]
        return dict(out)

    return {
        # Base
        'id': bug.id,
        'bugzilla_id': bug.bugzilla_id,
        'url': payload['url'],
        'summary' : bug_data['summary'],
        'keywords' : bug_data['keywords'],
        'flags_status' : _filter_flags(status_base_flag),
        'flags_tracking' : _filter_flags(tracking_base_flag),

        # Contributor structures
        'creator' : serialize_user(analysis['users']['creator']),
        'assignee' : serialize_user(analysis['users']['assignee']),
        'reviewers' : [serialize_user(r) for r in analysis['users']['reviewers']],

        # Stats
        'changes_size' : analysis.get('changes_size', 0),

        # Uplift request
        'uplift' : uplift,

        # Patches
        'patches' : analysis['patches'],
    }

def serialize_analysis(analysis, full=True):
    """
    Helper to serialize an analysis
    """
    out = {
        'id': analysis.id,
        'name': analysis.name,
        'count' : len(analysis.bugs),
        'parameters' : analysis.parameters,
    }

    if full:
        # Add bugs
        out['bugs'] = [serialize_bug(b) for b in analysis.bugs if b.payload]
    else:
        out['bugs'] = []

    return out

