# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from libmozdata.bugzilla import Bugzilla
from libmozdata.bugzilla import BugzillaUser

from cli_common.log import get_logger

logger = get_logger(__name__)


CANCELLED_UPLIFT = '''
Sorry, Uplift Bot failed to merge these patches onto mozilla-{}:

{}

Please ensure your patches apply cleanly, then request uplift again.
'''


def use_bugzilla(bugzilla_url, bugzilla_token=None):
    '''
    Configure Bugzilla access (URL + token)
    '''
    # Patch libmozdata configuration
    # TODO: Fix config calls in libmozdata
    # os.environ['LIBMOZDATA_CFG_BUGZILLA_URL'] = bugzilla_url
    # set_config(ConfigEnv())
    Bugzilla.URL = bugzilla_url
    Bugzilla.API_URL = bugzilla_url + '/rest/bug'
    Bugzilla.ATTACHMENT_API_URL = Bugzilla.API_URL + '/attachment'
    BugzillaUser.URL = bugzilla_url
    BugzillaUser.API_URL = bugzilla_url + '/rest/user'
    if bugzilla_token is not None:
        Bugzilla.TOKEN = bugzilla_token
        BugzillaUser.TOKEN = bugzilla_token


def list_bugs(query):
    '''
    List all the bugs from a Bugzilla query
    '''
    def _bughandler(bug, data):
        bugid = bug['id']
        data[bugid] = bug

    def _attachmenthandler(attachments, bugid, data):
        data[int(bugid)] = attachments

    bugs, attachments = {}, {}

    bz = Bugzilla(query,
                  bughandler=_bughandler,
                  attachmenthandler=_attachmenthandler,
                  bugdata=bugs,
                  attachmentdata=attachments)
    bz.get_data().wait()

    # Map attachments on bugs
    for bugid, _attachments in attachments.items():
        if bugid not in bugs:
            continue
        bugs[bugid]['attachments'] = _attachments

    return bugs


def load_users(analysis):
    '''
    Load users linked through roles to an analysis
    '''
    assert analysis is not None, \
        'Missing bug analysis'

    roles = {}

    def _extract_user(user_data, role):
        # Support multiple input structures
        if user_data is None:
            return
        elif isinstance(user_data, dict):
            if 'id' in user_data:
                key = user_data['id']
            elif 'email' in user_data:
                key = user_data['email']
            else:
                raise Exception('Invalid user data : no id or email')

        elif isinstance(user_data, str):
            key = user_data
        else:
            raise Exception('Invalid user data : unsupported format')

        if key not in roles:
            roles[key] = []
        roles[key].append(role)

    # Extract users keys & roles
    _extract_user(analysis['users'].get('creator'), 'creator')
    _extract_user(analysis['users'].get('assignee'), 'assignee')
    for r in analysis['users']['reviewers']:
        _extract_user(r, 'reviewer')
    _extract_user(analysis['uplift_author'], 'uplift_author')

    def _handler(user, data):
        # Store users with their roles
        user['roles'] = roles.get(user['id'], roles.get(user['email'], []))
        data.append(user)

    # Finally fetch clean users data through Bugzilla
    out = []
    BugzillaUser(user_names=roles.keys(),
                 user_handler=_handler,
                 user_data=out).wait()
    return out


def cancel_uplift_request(merge_test, read_only=True):
    '''
    Cancel a patch uplift request
    '''
    bugid = str(merge_test.bugzilla_id)
    branch = merge_test.branch.decode('utf-8')
    flag_name = 'approval-mozilla-' + branch
    flag_reset_payload = {
        'flags': [
            {
                'name': flag_name,
                'status': 'X'
            },
        ],
    }

    def _attachmenthandler(attachments, bugid, needinfos):
        for attachment in attachments:
            flags = [f for f in attachment['flags'] if f['name'] == flag_name]
            if len(flags) > 0:
                # Remember who requested this uplift, in order to needinfo them
                # later.
                needinfos.add(flags[0]['setter'])
                attachment_id = str(attachment['id'])
                logger.info('Resetting attachment flag:', bz_id=bugid, attachment_id=attachment_id, flag_name=flag_name)
                if read_only:
                    logger.info('...skipped resetting attachment flag: READ_ONLY')
                else:
                    Bugzilla([attachment_id]).put(flag_reset_payload, attachment=True)

    # Reset all uplift request flags in this bug's attachments.
    needinfos = set()
    Bugzilla(bugids=[bugid],
             attachmenthandler=_attachmenthandler,
             attachmentdata=needinfos).wait()

    merge_results = []
    for revision, result in merge_test.results.items():
        merge_result = '* Merge {} for commit {} (parent {})'.format(result.status, revision, result.parent)
        if (result.message):
            merge_result += ':\n{}'.format(result.message)
        merge_results.append(merge_result)

    comment_body = CANCELLED_UPLIFT.format(branch, '\n\n'.join(merge_results))
    comment_payload = {
        'comment': {
            'body': comment_body,
        },
        'flags': [
             {
                 'name': 'needinfo',
                 'requestee': needinfo,
                 'status': '?',
                 'new': 'true',  # don't remove pre-existing needinfos
             }
             for needinfo in needinfos
        ],
    }

    # Post comment and needinfos.
    logger.info('Posting comment and needinfos:', bz_id=bugid, comment_body=comment_body, needinfos=needinfos)
    if read_only:
        logger.info('...skipped posting comment and needinfos: READ_ONLY')
    else:
        Bugzilla(bugids=[bugid]).put(comment_payload)
