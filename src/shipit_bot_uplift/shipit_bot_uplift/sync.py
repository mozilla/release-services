# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import taskcluster
import itertools
import operator
import dateutil.parser
import os

from shipit_bot_uplift.helpers import (
    compute_dict_hash, read_hosts
)
from shipit_bot_uplift.mercurial import Repository
from shipit_bot_uplift.api import api_client
from shipit_bot_uplift.report import Report
from shipit_bot_uplift import log
from libmozdata import bugzilla, versions
from libmozdata.patchanalysis import bug_analysis, parse_uplift_comment


logger = log.get_logger('shipit_bot')


def analysis2branch(analysis):
    """
    Convert an analysis dict into a mercurial
    branch name (special case for esrXX)
    """
    if analysis['name'] == 'esr':
        return 'esr{}'.format(analysis['version'])
    return analysis['name'].lower()


class MergeTest(object):
    """
    A merge test for a specific patch
    against a branch
    """
    def __init__(self, bugzilla_id, branch, revision, last_status=None):
        self.bugzilla_id = bugzilla_id
        self.branch = branch
        self.revision = revision
        self.revision_parent = None
        self.last_status = last_status
        self.status = None
        self.message = None

    def update_result(self, revision_parent, merge_status, message):
        """
        Store a new patch status on backend
        """
        assert isinstance(merge_status, bool)
        assert isinstance(revision_parent, str)
        assert isinstance(message, str)
        self.revision_parent = revision_parent
        self.status = merge_status
        self.message = message

        # Publish as a new patch status
        data = {
            'revision': self.revision.decode('utf-8'),
            'revision_parent': revision_parent,
            'merged': merge_status,
            'branch': self.branch.decode('utf-8'),
            'message': message,
        }
        try:
            api_client.create_patch_status(self.bugzilla_id, data)
            logger.info('Created new patch status', **data)
        except Exception as err:
            logger.error('Failed to create patch status', err=err)
            return False

        return True


class BugSync(object):
    """
    Helper class to sync bugs between
    Bugzilla & remote server
    """
    def __init__(self, bugzilla_id):
        self.bugzilla_id = bugzilla_id
        self.on_remote = []
        self.on_bugzilla = []
        self.bug_data = None
        self.analysis = None

    def setup_remote(self, analysis):
        """
        Bug is on remote (backend)
        """
        self.on_remote.append(analysis['id'])
        logger.debug('On remote', bz_id=self.bugzilla_id)

    def setup_bugzilla(self, analysis, bug_data):
        """
        Bug is on Bugzilla, store data
        Only when the uplift is pending (tag '?' on attachment)
        """
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
        """
        Update bug used in this sync
        """

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
    def testable_patches(self):
        """
        List all patches in current analysis
        as (revision, branch) tuples
        """
        assert self.analysis is not None, \
            'Missing bug analysis'

        last_status = {}
        try:
            # Load patch status for this bug
            # And group them by revision & branch
            patch_status = api_client.list_patch_status(self.bugzilla_id)
            grouper = operator.itemgetter('revision', 'branch')
            groups = itertools.groupby(sorted(patch_status, key=grouper), grouper)  # noqa

            for keys, statuses in groups:

                # Sort groups by datetime
                statuses = sorted(
                    statuses,
                    key=lambda s: dateutil.parser.parse(s['created']),
                    reverse=True
                )
                keys = tuple(map(lambda x: x.encode('utf-8'), keys))
                last_status[keys] = statuses[0]
        except Exception as e:
            logger.warn('No patch status', bz_id=self.bugzilla_id, error=e)

        def _link_status(revision, analysis):
            # Cleanup inputs
            revision = isinstance(revision, int) \
                and str(revision).encode('utf-8') \
                or revision.encode('utf-8')
            branch = analysis2branch(analysis).encode('utf-8')

            # Retrieve last status
            keys = (revision, branch)
            return MergeTest(
                self.bugzilla_id,
                branch,
                revision,
                last_status.get(keys)
            )

        return [
            _link_status(revision, analysis)
            for revision in self.analysis['patches'].keys()
            for analysis in self.on_bugzilla
        ]

    def build_payload(self, bugzilla_url):
        """
        Build final paylaod, sent to remote server
        """
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
        """
        Load users linked through roles to an analysis
        """
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
        """
        Extract versions from bug attachments
        """
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
    """
    Update all analysis data
    """
    def __init__(self, bugzilla_url, bugzilla_token=None):
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

    def run(self):
        raise NotImplementedError

    def use_cache(self, cache_root):
        """
        Setup cache directory
        User to clone Mercurial repository for merge checks
        """

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
        """
        List all the bugs from a Bugzilla query
        """
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


class BotRemote(Bot):
    """
    Use a distant shipit api server
    to store processed analysis
    """
    def __init__(self, secrets_path, client_id=None, access_token=None):
        # Start by loading secrets from Taskcluster
        secrets = self.load_secrets(
            self.build_tc_options('secrets/v1', client_id, access_token),
            secrets_path
        )

        # Setup credentials for Shipit api
        api_client.setup(
            secrets['API_URL'],
            secrets.get('TASKCLUSTER_CLIENT_ID', client_id),
            secrets.get('TASKCLUSTER_ACCESS_TOKEN', access_token)
        )

        super(BotRemote, self).__init__(
            secrets['BUGZILLA_URL'],
            secrets['BUGZILLA_TOKEN']
        )
        self.sync = {}  # init

        # Init report
        options = self.build_tc_options('notify/v1', client_id, access_token)
        self.report = Report(options, [
            'babadie@mozilla.com',
            'sledru@mozilla.com',
        ])

    def build_tc_options(self, service_endpoint, client_id=None, access_token=None):  # noqa
        """
        Build Taskcluster credentials options
        """

        if client_id and access_token:
            # Use provided credentials
            tc_options = {
                'credentials': {
                    'clientId': client_id,
                    'accessToken': access_token,
                }
            }

        else:
            # Get taskcluster proxy host
            # as /etc/hosts is not used in the Nix image (?)
            hosts = read_hosts()
            if 'taskcluster' not in hosts:
                raise Exception('Missing taskcluster in /etc/hosts')

            # Load secrets from TC task context
            # with taskclusterProxy
            base_url = 'http://{}/{}'.format(
                hosts['taskcluster'],
                service_endpoint
            )
            logger.info('Taskcluster Proxy enabled', url=base_url)
            tc_options = {
                'baseUrl': base_url
            }

        return tc_options

    def load_secrets(self, tc_options, secrets_path):
        """
        Load Taskcluster secrets
        """
        # Check mandatory keys in secrets
        secrets = taskcluster.Secrets(tc_options).get(secrets_path)
        secrets = secrets['secret']
        required = ('BUGZILLA_URL', 'BUGZILLA_TOKEN', 'API_URL')
        for req in required:
            if req not in secrets:
                raise Exception('Missing value {} in Taskcluster secret value {}'.format(req, secrets_path))  # noqa

        return secrets

    def get_bug_sync(self, bugzilla_id):
        if bugzilla_id not in self.sync:
            # Init new bug sync
            bug = BugSync(bugzilla_id)
            self.sync[bugzilla_id] = bug

        return self.sync[bugzilla_id]

    def run(self, only=None):
        """
        Build bug analysis for a specified Bugzilla query
        Used by taskcluster - no db interaction
        """
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
                    merge_tests += sync.testable_patches

            elif len(sync.on_remote) > 0:
                self.delete_bug(sync)

        # Sort merge tests by branches
        logger.info('Running merge tests', nb=len(merge_tests))
        merge_tests = sorted(merge_tests, key=lambda x: x.branch)
        groups = itertools.groupby(merge_tests, lambda x: x.branch)
        for branch, tests in groups:

            # Switch to branch and get parent revision
            parent = self.repository.checkout(branch)

            # Run all the merge tests for this revision
            for merge_test in tests:
                self.run_merge_test(merge_test, parent)

        # Send report
        self.report.send()

    def update_bug(self, sync):
        """
        Update specific bug
        """
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
        except Exception as e:
            logger.error('Failed to add bug #{} : {}'.format(sync.bugzilla_id, e))  # noqa
            return False

        return True

    def run_merge_test(self, merge_test, parent):
        """
        Try to merge a patch on current repository branch
        """
        assert isinstance(merge_test, MergeTest)
        assert merge_test.status is None, \
            'Already ran this merge test.'

        if merge_test.last_status and parent == merge_test.last_status['revision_parent']: # noqa
            logger.info('Skiping merge test : same parent', revision=merge_test.revision, branch=merge_test.branch, parent=parent)  # noqa
            return

        # Run the merge test
        merged, message = self.repository.is_mergeable(merge_test.revision)
        updated = merge_test.update_result(parent, merged, message)

        # Always cleanup
        self.repository.cleanup(parent)

        # Save invalid merge in report
        if updated and not merged:
            self.report.add_invalid_merge(merge_test)

    def delete_bug(self, sync):
        """
        Remove bugs from remote server
        """
        assert isinstance(sync, BugSync), \
            'Use BugSync instance'
        try:
            api_client.delete_bug(sync.bugzilla_id)
            logger.info('Deleted bug', bz_id=sync.bugzilla_id, analysis=sync.on_remote)  # noqa
        except Exception as e:
            logger.warning('Failed to delete bug #{} : {}'.format(sync.bugzilla_id, e))  # noqa
