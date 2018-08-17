# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
import os

from libmozdata import bugzilla
from libmozdata import versions
from libmozdata.patchanalysis import bug_analysis
from libmozdata.patchanalysis import parse_uplift_comment

from cli_common.log import get_logger
from shipit_bot_uplift.api import NotFound
from shipit_bot_uplift.api import api_client
from shipit_bot_uplift.helpers import compute_dict_hash
from shipit_bot_uplift.mercurial import Repository
from shipit_bot_uplift.merge import MergeTest
from shipit_bot_uplift.report import Report

logger = get_logger(__name__)


def analysis2branch(analysis):
    '''
    Convert an analysis dict into a mercurial
    branch name (special case for esrXX)
    '''
    if analysis['name'] == 'esr':
        return 'esr{}'.format(analysis['version'])
    return analysis['name'].lower()


class BugSync(object):
    '''
    Helper class to sync bugs between
    Bugzilla & remote server
    '''
    def __init__(self, bugzilla_id):
        self.bugzilla_id = bugzilla_id
        self.on_remote = []
        self.on_bugzilla = []
        self.bug_data = None
        self.analysis = None

    def setup_remote(self, analysis):
        '''
        Bug is on remote (backend)
        '''
        self.on_remote.append(analysis['id'])
        logger.debug('On remote', bz_id=self.bugzilla_id)

    def setup_bugzilla(self, analysis, bug_data):
        '''
        Bug is on Bugzilla, store data
        Only when the uplift is pending (tag '?' on attachment)
        '''
        if self.bug_data is None:
            self.bug_data = bug_data

        # Check the versions contain current analysis
        versions = self.list_versions()
        version_pending = '{} ?'.format(analysis2branch(analysis))
        if version_pending not in versions:
            logger.warn('Skipping bugzilla', bz_id=self.bugzilla_id, version=version_pending, versions=list(versions.keys()))  # noqa
            return

        self.on_bugzilla.append(analysis)
        logger.debug('On bugzilla', bz_id=self.bugzilla_id)

    def update(self):
        '''
        Update bug used in this sync
        '''

        # Skip when it's already processed in instance
        if self.analysis is not None:
            logger.warn('Bug {} already processed.'.format(self.bugzilla_id))
            return True

        # Do patch analysis
        try:
            self.analysis = bug_analysis(self.bugzilla_id, 'release')
        except Exception as e:
            logger.error('Patch analysis failed on {} : {}'.format(self.bugzilla_id, e))  # noqa
            # TODO: Add to report
            return False

        # Build html version of uplift comment
        if self.analysis.get('uplift_comment'):
            self.analysis['uplift_comment']['html'] = parse_uplift_comment(
                self.analysis['uplift_comment']['text'], self.bugzilla_id)

        return True

    @property
    def merge_tests(self):
        '''
        List all available merge tests
        One per uplift request
        '''
        assert self.analysis is not None, \
            'Missing bug analysis'

        return [
            MergeTest(
                self.bugzilla_id,
                analysis2branch(analysis).encode('utf-8'),
                self.analysis['patches']
            )
            for analysis in self.on_bugzilla
        ]

    def build_payload(self, bugzilla_url):
        '''
        Build final paylaod, sent to remote server
        '''
        # Compute the hash of the new bug
        bug_hash = compute_dict_hash(self.bug_data)

        # Build internal payload
        return {
            'bugzilla_id': self.bugzilla_id,
            'analysis': [a['id'] for a in self.on_bugzilla],
            'payload': {
                'url': '{}/{}'.format(bugzilla_url, self.bugzilla_id),
                'bug': self.bug_data,
                'analysis': self.analysis,
                'users': self.load_users(),
                'versions': self.list_versions(),
            },
            'payload_hash': bug_hash,
        }

    def load_users(self):
        '''
        Load users linked through roles to an analysis
        '''
        assert self.analysis is not None, \
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
        _extract_user(self.analysis['users'].get('creator'), 'creator')
        _extract_user(self.analysis['users'].get('assignee'), 'assignee')
        for r in self.analysis['users']['reviewers']:
            _extract_user(r, 'reviewer')
        _extract_user(self.analysis['uplift_author'], 'uplift_author')

        def _handler(user, data):
            # Store users with their roles
            user['roles'] = roles.get(user['id'], roles.get(user['email'], []))
            data.append(user)

        # Finally fetch clean users data through Bugzilla
        out = []
        bugzilla.BugzillaUser(user_names=roles.keys(),
                              user_handler=_handler,
                              user_data=out).wait()
        return out

    def list_versions(self):
        '''
        Extract versions from bug attachments
        '''
        approval_base_flag = 'approval-mozilla-'
        versions = {}
        for a in self.bug_data.get('attachments', []):
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

        return versions


class Bot(object):
    '''
    Update all analysis data
    '''
    def __init__(self, app_channel, notification_emails=[]):
        self.app_channel = app_channel
        self.sync = {}

        # Init report
        self.report = Report(notification_emails)

    def use_bugzilla(self, bugzilla_url, bugzilla_token=None):
        '''
        Setup bugzilla usage (url + token)
        '''
        self.bugs = {}
        self.repository = None
        self.bugzilla_url = bugzilla_url

        # Patch libmozdata configuration
        # TODO: Fix config calls in libmozdata
        # os.environ['LIBMOZDATA_CFG_BUGZILLA_URL'] = self.bugzilla_url
        # set_config(ConfigEnv())
        bugzilla.Bugzilla.URL = self.bugzilla_url
        bugzilla.Bugzilla.API_URL = self.bugzilla_url + '/rest/bug'
        bugzilla.BugzillaUser.URL = self.bugzilla_url
        bugzilla.BugzillaUser.API_URL = self.bugzilla_url + '/rest/user'
        if bugzilla_token is not None:
            bugzilla.Bugzilla.TOKEN = bugzilla_token
            bugzilla.BugzillaUser.TOKEN = bugzilla_token

        logger.info('Use bugzilla server', url=self.bugzilla_url)

    def use_cache(self, cache_root):
        '''
        Setup cache directory
        User to clone Mercurial repository for merge checks
        '''

        # Check cache directory
        assert os.path.isdir(cache_root), \
            'Missing cache root {}'.format(cache_root)
        assert os.access(cache_root, os.W_OK | os.X_OK), \
            'Cache root {} is not writable'.format(cache_root)
        logger.info('Using cache', root=cache_root)

        # Init local copy of mozilla-unified
        self.repository = Repository(
            'https://hg.mozilla.org/mozilla-unified',
            cache_root,
        )

    def list_bugs(self, query):
        '''
        List all the bugs from a Bugzilla query
        '''
        def _bughandler(bug, data):
            bugid = bug['id']
            data[bugid] = bug

        def _attachmenthandler(attachments, bugid, data):
            data[int(bugid)] = attachments

        bugs, attachments = {}, {}

        bz = bugzilla.Bugzilla(query,
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

    def get_bug_sync(self, bugzilla_id):
        if bugzilla_id not in self.sync:
            # Init new bug sync
            bug = BugSync(bugzilla_id)
            self.sync[bugzilla_id] = bug

        return self.sync[bugzilla_id]

    def run(self, only=None):
        '''
        Build bug analysis for a specified Bugzilla query
        Used by taskcluster - no db interaction
        '''
        assert self.repository is not None, \
            'Missing mozilla repository'

        # Update HG central to get new patches revisions
        self.repository.checkout(b'central')

        # Get official mozilla release versions
        current_versions = versions.get(True)

        # Load all analysis
        for analysis in api_client.list_analysis():

            # Check version number
            current_version = current_versions.get(analysis['name'])
            if current_version is None:
                raise Exception('Unsupported analysis {}'.format(analysis['name']))  # noqa
            if analysis['version'] != current_version:
                data = {
                    'version': current_version,
                }
                analysis = api_client.update_analysis(analysis['id'], data)
                logger.info('Updated analysis version', name=analysis['name'], version=analysis['version'])  # noqa

            # Mark bugs already in analysis
            logger.info('List remote bugs', name=analysis['name'])
            analysis_details = api_client.get_analysis(analysis['id'])
            for bug in analysis_details['bugs']:
                sync = self.get_bug_sync(bug['bugzilla_id'])
                sync.setup_remote(analysis)

            # Get bugs from bugzilla for this analysis
            logger.info('List bugzilla bugs', name=analysis['name'])
            raw_bugs = self.list_bugs(analysis['parameters'])
            for bugzilla_id, bug_data in raw_bugs.items():
                sync = self.get_bug_sync(bugzilla_id)
                sync.setup_bugzilla(analysis, bug_data)

        merge_tests = []
        for sync in self.sync.values():

            # Filter bugs when 'only' is filled
            if only is not None and sync.bugzilla_id not in only:
                logger.debug('Skip', bz_id=sync.bugzilla_id)
                continue

            if len(sync.on_bugzilla) > 0:
                if self.update_bug(sync):
                    merge_tests += sync.merge_tests

            elif len(sync.on_remote) > 0:
                self.delete_bug(sync)

        # Sort merge tests by branches
        logger.info('Running merge tests', nb=len(merge_tests))
        merge_tests = sorted(merge_tests, key=lambda x: x.branch)
        groups = itertools.groupby(merge_tests, lambda x: x.branch)
        for branch, tests in groups:

            # Switch to branch and get parent revision
            self.repository.checkout(branch)

            # Run all the merge tests for this revision
            for merge_test in tests:
                self.run_merge_test(merge_test)

        # Send report
        self.report.send(self.app_channel)

    def update_bug(self, sync):
        '''
        Update specific bug
        '''
        assert isinstance(sync, BugSync), \
            'Use BugSync instance'

        # Do patch analysis on bugs
        logger.info('Started bug analysis', bz_id=sync.bugzilla_id)
        if not sync.update():
            return False

        # Send payload to server
        try:
            payload = sync.build_payload(self.bugzilla_url)
            api_client.create_bug(payload)
            logger.info('Added bug', bz_id=sync.bugzilla_id, analysis=[a['name'] for a in sync.on_bugzilla])  # noqa
        except NotFound:
            logger.info('Bug not found, not updated.', bz_id=sync.bugzilla_id)
        except Exception as e:
            logger.error('Failed to add bug #{} : {}'.format(sync.bugzilla_id, e))  # noqa
            return False

        return True

    def run_merge_test(self, merge_test):
        '''
        Try to merge a patch on current repository branch
        '''
        assert isinstance(merge_test, MergeTest)
        assert len(merge_test.results) == 0, \
            'Already ran this merge test.'

        # Run the merge test on repository
        if not merge_test.run(self.repository):
            return

        # Always cleanup
        self.repository.cleanup()

        # Save invalid merge in report
        if not merge_test.is_valid():
            self.report.add_invalid_merge(merge_test)

    def delete_bug(self, sync):
        '''
        Remove bugs from remote server
        '''
        assert isinstance(sync, BugSync), \
            'Use BugSync instance'
        try:
            api_client.delete_bug(sync.bugzilla_id)
            logger.info('Deleted bug', bz_id=sync.bugzilla_id, analysis=sync.on_remote)  # noqa
        except NotFound:
            logger.info('Bug not found, not deleted.', bz_id=sync.bugzilla_id)
        except Exception as e:
            logger.warning('Failed to delete bug #{} : {}'.format(sync.bugzilla_id, e))  # noqa
