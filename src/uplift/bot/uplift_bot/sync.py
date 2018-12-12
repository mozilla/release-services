# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import itertools
import os
import tempfile

from libmozdata import versions
from libmozdata.patchanalysis import bug_analysis
from libmozdata.patchanalysis import parse_uplift_comment
from libmozdata.patchanalysis import uplift_info

from cli_common.log import get_logger
from uplift_bot.api import NotFound
from uplift_bot.api import api_client
from uplift_bot.bugzilla import cancel_uplift_request
from uplift_bot.bugzilla import list_bugs
from uplift_bot.bugzilla import load_users
from uplift_bot.bugzilla import use_bugzilla
from uplift_bot.config import UPLIFT_STATUS
from uplift_bot.helpers import compute_dict_hash
from uplift_bot.mercurial import Repository
from uplift_bot.merge import MergeTest
from uplift_bot.report import Report

logger = get_logger(__name__)

STATUS_APPROVED = '+'
STATUS_PENDING = '?'


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
        self.uplifts = None

    def setup_remote(self, analysis):
        '''
        Bug is on remote (backend)
        '''
        self.on_remote.append(analysis['id'])
        logger.debug('On remote', bz_id=self.bugzilla_id)

    def setup_bugzilla(self, analysis, bug_data, status):
        '''
        Bug is on Bugzilla, store data
        Only when the requested version is available
        '''
        assert status in (STATUS_APPROVED, STATUS_PENDING)
        if self.bug_data is None:
            self.bug_data = bug_data

        # Check the versions contain current analysis
        versions = self.list_versions()
        version = '{} {}'.format(analysis2branch(analysis), status)
        if version not in versions:
            logger.warn('Skipping bugzilla', bz_id=self.bugzilla_id, version=version, versions=list(versions.keys()))  # noqa
            return

        self.on_bugzilla.append((analysis, status))
        logger.info('On bugzilla', bz_id=self.bugzilla_id, version=version)

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
            logger.info('Bug analysis', bz_id=self.bugzilla_id)
            self.analysis = bug_analysis(self.bugzilla_id, 'release')
        except Exception as e:
            logger.error('Patch analysis failed on {} : {}'.format(self.bugzilla_id, e))  # noqa
            # TODO: Add to report
            return False

        # Build html version of uplift comment
        if self.analysis.get('uplift_comment'):
            self.analysis['uplift_comment']['html'] = parse_uplift_comment(
                self.analysis['uplift_comment']['text'], self.bugzilla_id)

        # Get all extras uplift infos for approved requests
        branches = set([
            analysis2branch(analysis)
            for analysis, status in self.on_bugzilla
            if status == STATUS_APPROVED
        ])
        self.uplifts = {}
        for branch in branches:
            logger.info('Retrieves uplift infos', bz_id=self.bugzilla_id, branch=branch)
            self.uplifts[branch] = uplift_info(self.bugzilla_id, branch)

        return True

    def build_merge_tests(self):
        '''
        List all available merge tests
        One per uplift request
        '''
        assert self.analysis is not None, \
            'Missing bug analysis'
        assert self.uplifts is not None, \
            'Missing uplifts infos'

        def _build(analysis, status):
            branch = analysis2branch(analysis)
            uplift = self.uplifts.get(branch)

            return MergeTest(
                self.bugzilla_id,
                branch.encode('utf-8'),
                status,
                self.analysis['patches'],
                uplift and uplift.get('uplift_reviewer'),
            )

        return [
            _build(analysis, status)
            for analysis, status in self.on_bugzilla
        ]

    def build_payload(self, bugzilla_url):
        '''
        Build final payload, sent to remote server
        '''
        # Compute the hash of the new bug
        bug_hash = compute_dict_hash(self.bug_data)

        # Build internal payload
        return {
            'bugzilla_id': self.bugzilla_id,
            'analysis': [a['id'] for a, status in self.on_bugzilla if status == STATUS_PENDING],
            'payload': {
                'url': '{}/{}'.format(bugzilla_url, self.bugzilla_id),
                'bug': self.bug_data,
                'analysis': self.analysis,
                'users': load_users(self.analysis),
                'versions': self.list_versions(),
            },
            'payload_hash': bug_hash,
        }

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
        self.ssh_key_path = None
        self.sync = {}

        # Init report
        self.report = Report(notification_emails)

    def use_bugzilla(self, bugzilla_url, bugzilla_token=None, read_only=True, comment_only=False):
        '''
        Setup bugzilla usage (url + token)
        '''
        self.bugs = {}
        self.repository = None
        self.bugzilla_url = bugzilla_url
        self.bugzilla_read_only = read_only
        self.bugzilla_comment_only = comment_only

        use_bugzilla(bugzilla_url, bugzilla_token)
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

    def use_mercurial_remote(self, uri, ssh_key, ssh_user=None):
        '''
        Configure repository remote destination
        '''
        # Write ssh key to temp file
        _, self.ssh_key_path = tempfile.mkstemp(suffix='.key')
        with open(self.ssh_key_path, 'w') as f:
            f.write(ssh_key)

        # Build ssh config
        conf = {
            'IdentityFile': self.ssh_key_path,
        }
        if ssh_user:
            conf['User'] = ssh_user
        self.repository.remote_ssh_config = conf

        # Setup remote uri
        if isinstance(uri, str):
            uri = uri.encode('utf-8')
        self.repository.remote_uri = uri
        logger.info('Will push uplifts to', uri=self.repository.remote_uri)

    def get_bug_sync(self, bugzilla_id):
        if bugzilla_id not in self.sync:
            # Init new bug sync
            bug = BugSync(bugzilla_id)
            self.sync[bugzilla_id] = bug

        return self.sync[bugzilla_id]

    def run(self, uplift_status=UPLIFT_STATUS, only=None):
        '''
        Build bug analysis for a specified Bugzilla query
        Used by taskcluster - no db interaction
        '''
        assert isinstance(uplift_status, tuple)
        assert len(uplift_status) > 0, \
            'No uplift status'
        assert set(UPLIFT_STATUS).issuperset(uplift_status), \
            'Invalid uplift status'
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
            if 'pending' in uplift_status:
                logger.info('List bugzilla pending bugs', name=analysis['name'])
                raw_bugs = list_bugs(analysis['parameters_pending'])
                for bugzilla_id, bug_data in raw_bugs.items():
                    sync = self.get_bug_sync(bugzilla_id)
                    sync.setup_bugzilla(analysis, bug_data, STATUS_PENDING)
            else:
                logger.info('Skipped bugzilla pending bugs', name=analysis['name'])

            # Load approved bugs, to be tested for merges
            if 'approved' in uplift_status:
                logger.info('List bugzilla approved bugs', name=analysis['name'])
                raw_bugs = list_bugs(analysis['parameters_approved'])
                for bugzilla_id, bug_data in raw_bugs.items():
                    sync = self.get_bug_sync(bugzilla_id)
                    sync.setup_bugzilla(analysis, bug_data, STATUS_APPROVED)
            else:
                logger.info('Skipped bugzilla approved bugs', name=analysis['name'])

        merge_tests = []
        for sync in self.sync.values():

            # Filter bugs when 'only' is filled
            if only is not None and sync.bugzilla_id not in only:
                logger.debug('Skip', bz_id=sync.bugzilla_id)
                continue

            if len(sync.on_bugzilla) > 0:
                if self.update_bug(sync):
                    merge_tests += sync.build_merge_tests()

            elif len(sync.on_remote) > 0:
                self.delete_bug(sync)

        # Sort merge tests by branches
        logger.info('Running merge tests', nb=len(merge_tests))
        merge_tests = sorted(merge_tests, key=lambda x: x.branch)
        groups = itertools.groupby(merge_tests, lambda x: x.branch)
        pushed = []
        for branch, tests in groups:

            # Switch to branch and get parent revision
            self.repository.checkout(branch)

            # Run all the merge tests for this revision
            # Saving only the new pushes
            pushed += [
                merge_test
                for merge_test in tests
                if self.run_merge_test(merge_test)
            ]

        # Remove temporary ssh key
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            os.unlink(self.ssh_key_path)

        # Send report
        self.report.send(self.app_channel, pushed)

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

        # Skip bug payload update for bugs with r+ status only
        skip_update = all([
            status == STATUS_APPROVED
            for _, status in sync.on_bugzilla
        ])
        if skip_update:
            return True

        # Send payload to server
        try:
            payload = sync.build_payload(self.bugzilla_url)
            api_client.create_bug(payload)
            logger.info('Added bug', bz_id=sync.bugzilla_id, analysis=[a['name'] for a,_ in sync.on_bugzilla])  # noqa
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

        if merge_test.is_valid():
            if merge_test.status == STATUS_PENDING:
                logger.info('Skipping push on pending bug', merge_test=merge_test)
            elif self.repository.remote_uri and merge_test.branch_rebased:
                # Returns True when a new branch has been pushed
                logger.info('Pushing on remote repository', branch=merge_test.branch_rebased)
                return self.repository.push(merge_test.branch_rebased)
            else:
                logger.info('Skipping push on remote repository, not configured')
        else:

            # Save invalid merge in report, and cancel the uplift request
            self.report.add_invalid_merge(merge_test)
            cancel_uplift_request(merge_test, self.bugzilla_read_only, self.bugzilla_comment_only)

        # No push
        return False

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
