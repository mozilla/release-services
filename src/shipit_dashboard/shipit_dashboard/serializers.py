
def _serialize_bug(bug):
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
            'author' : {
                'email' : author['name'], # weird :/
                'real_name' : author['real_name'],
            },
            'comment' : comment['raw_text'],
        }

    status_base_flag = 'cf_status_'
    tracking_base_flag = 'cf_tracking_'

    return {
        # Base
        'id': bug.id,
        'bugzilla_id': bug.bugzilla_id,
        'summary' : bug_data['summary'],
        'keywords' : bug_data['keywords'],
        'flags_status' : dict([(k.replace(status_base_flag, '', 1) ,v) for k,v in bug_data.items() if k.startswith(status_base_flag)]),
        'flags_tracking' : dict([(k.replace(tracking_base_flag, '', 1) ,v) for k,v in bug_data.items() if k.startswith(tracking_base_flag)]),


        # Contributor structures
        'creator' : analysis['users']['creator'],
        'assignee' : analysis['users']['assignee'],
        'reviewers' : [{
            'email' : r,
            'real_name' : r,
        } for r in analysis['users']['reviewers']],

        # Stats
        'changes_size' : analysis.get('changes_size', 0),

        # Uplift request
        'uplift' : uplift,
    }

def serialize_analysis(analysis, full=True):
    """
    Helper to serialize an analysis
    """
    out = {
        'id': analysis.id,
        'name': analysis.name,
        'count' : len(analysis.bugs),
    }

    if full:
        # Add bugs
        out['bugs'] = [_serialize_bug(b) for b in analysis.bugs if b.payload]
    else:
        out['bugs'] = []

    return out

