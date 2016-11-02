# coding=utf-8
from releng_common.db import db
from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.helpers import compute_dict_hash
from shipit_dashboard.encoder import ShipitJSONEncoder
from libmozdata.patchanalysis import bug_analysis, parse_uplift_comment
from libmozdata import bugzilla
from sqlalchemy.orm.exc import NoResultFound
from flask.cli import with_appcontext
from flask import current_app
from flask import json
import logging
import requests
import mohawk
import pickle
import click
import os

logger = logging.getLogger(__name__)

class BugSync(object):
    """
    Helper class to sync bugs between
    Bugzilla & remote server
    """
    def __init__(self, bugzilla_id):
        self.bugzilla_id = bugzilla_id
        self.on_remote = []
        self.on_bugzilla = []
        self.raw = None

class Workflow(object):
    """
    Update all analysis data
    """
    def __init__(self, bugzilla_url, bugzilla_token=None):
        self.bugs = {}
        self.bugzilla_url = bugzilla_url

        # Patch libmozdata configuration
        # TODO: Fix config calls in libmozdata
        #os.environ['LIBMOZDATA_CFG_BUGZILLA_URL'] = self.bugzilla_url
        #set_config(ConfigEnv())
        bugzilla.Bugzilla.URL = self.bugzilla_url
        bugzilla.Bugzilla.API_URL = self.bugzilla_url + '/rest/bug'
        bugzilla.BugzillaUser.URL = self.bugzilla_url
        bugzilla.BugzillaUser.API_URL = self.bugzilla_url + '/rest/user'
        if bugzilla_token is not None:
            bugzilla.Bugzilla.TOKEN = bugzilla_token
            bugzilla.BugzillaUser.TOKEN = bugzilla_token

        logger.info('Use bugzilla server {}'.format(self.bugzilla_url))

    def run(self):
        raise NotImplementedError

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

        bz = bugzilla.Bugzilla(query, bughandler=_bughandler, attachmenthandler=_attachmenthandler, bugdata=bugs, attachmentdata=attachments)
        bz.get_data().wait()

        # Map attachments on bugs
        for bugid, _attachments in attachments.items():
            if bugid not in bugs:
                continue
            bugs[bugid]['attachments'] = _attachments

        return bugs

    def update_bug(self, bug, use_db=True):
        """
        Update a bug
        """

        # Skip when it's already processed in instance
        bug_id = bug['id']
        if bug_id in self.bugs:
            logger.warn('Bug {} already processed.'.format(bug_id))
            return self.bugs[bug_id]

        # Compute the hash of the new bug
        bug_hash = compute_dict_hash(bug)

        if use_db:
            # Fetch or create existing bug result
            try:
                br = BugResult.query.filter_by(bugzilla_id=bug_id).one()
                logger.info('Update existing {}'.format(br))

                # Check the bug has changed since last update
                if br.payload_hash == bug_hash:
                    logger.info('Same bug hash, skip bug analysis {}'.format(br))
                    return br

            except NoResultFound:
                br = BugResult(bug_id)
                logger.info('Create new {}'.format(br))
        else:
            # Create a new instance
            br = BugResult(bug_id)
            logger.info('Create new {}'.format(br))

        # Do patch analysis
        try:
            analysis = bug_analysis(bug_id)
        except Exception as e:
            logger.error('Patch analysis failed on {} : {}'.format(bug_id, e))
            return

        # Build html version of uplift comment
        if analysis['uplift_comment']:
            analysis['uplift_comment']['html'] = parse_uplift_comment(analysis['uplift_comment']['text'], bug_id)

        payload = {
            'url' : '{}/{}'.format(self.bugzilla_url, bug['id']),
            'bug': bug,
            'analysis': analysis,
            'users' : self.load_users(analysis),
        }
        br.payload = use_db and pickle.dumps(payload, 2) or payload
        br.payload_hash = bug_hash
        logger.info('Updated payload of {}'.format(br))

        # Save in local cache
        self.bugs[bug_id] = br

        return br

    def load_users(self, analysis):
        """
        Load users linked through roles to an analysis
        """
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
        bugzilla.BugzillaUser(user_names=roles.keys(), user_handler=_handler, user_data=out).wait()
        return out

class WorkflowLocal(Workflow):
    """
    Use all analysis stored on local db
    and update them directly
    """

    def run(self):
        all_analysis = BugAnalysis.query.all()
        for analysis in all_analysis:

            # Get bugs from bugzilla, for all analysis
            logger.info('List bugs for {}'.format(analysis))
            raw_bugs = self.list_bugs(analysis.parameters)

            # Empty m2m relation
            for bug in analysis.bugs:
                bug.delete()

            # Do patch analysis on bugs
            for raw_bug in raw_bugs.values():
                bug = self.update_bug(raw_bug)

                # Save updated & linked bug
                if bug:
                    analysis.bugs.append(bug)
                    db.session.add(bug)
                    db.session.add(analysis)
                    db.session.commit()

class WorkflowRemote(Workflow):
    """
    Use a distant shipit api server
    to store processed analysis
    """
    def __init__(self, bugzilla_url, bugzilla_token, api_url, client_id, access_token):
        super(WorkflowRemote, self).__init__(bugzilla_url, bugzilla_token)
        self.api_url = api_url
        self.credentials = {
          'id' : client_id,
          'key' : access_token,
          'algorithm' : 'sha256',
        }
        self.sync = {} # init

    def make_request(self, method, url, data=''):
        """
        Make an HAWK authenticated request on remote server
        """
        request = getattr(requests, method)
        if not request:
            raise Exception('Invalid method {}'.format(method))

        # Build HAWK token
        url = self.api_url + url
        hawk = mohawk.Sender(self.credentials, url, method, content=data, content_type='application/json')

        # Send request
        headers = {
            'Authorization' : hawk.request_header,
            'Content-Type' : 'application/json',
        }
        response = request(url, data=data, headers=headers, verify=False)
        if not response.ok:
            raise Exception('Invalid response from {} {} : {}'.format(method, url, response.content))

        return response.json()

    def get_bug_sync(self, bugzilla_id):
        if bugzilla_id not in self.sync:
            # Init new bug sync
            bug = BugSync(bugzilla_id)
            self.sync[bugzilla_id] = bug

        return self.sync[bugzilla_id]

    def run(self):
        """
        Build bug analysis for a specified Bugzilla query
        Used by taskcluster - no db interaction
        """

        # Use custom json encoder to process timedeltas
        current_app.json_encoder = ShipitJSONEncoder

        # Load all analysis
        all_analysis = self.make_request('get', '/analysis')
        for analysis in all_analysis:

            # Mark bugs already in analysis
            logger.info('List remote bugs for {}'.format(analysis['name']))
            analysis_details = self.make_request('get', '/analysis/{}'.format(analysis['id']))
            syncs = map(self.get_bug_sync, [b['bugzilla_id'] for b in analysis_details['bugs']])
            for sync in syncs:
                sync.on_remote.append(analysis['id'])

            # Get bugs from bugzilla for this analysis
            logger.info('List bugzilla bugs for {}'.format(analysis['name']))
            raw_bugs = self.list_bugs(analysis['parameters'])
            for bugzilla_id, raw in raw_bugs.items():
                sync = self.get_bug_sync(bugzilla_id)
                if sync.raw is None:
                    sync.raw = raw
                sync.on_bugzilla.append(analysis['id'])

        for bugzilla_id, sync in self.sync.items():

            if len(sync.on_bugzilla) > 0:
                # Do patch analysis on bugs
                bug = self.update_bug(sync.raw, use_db=False)
                if not bug:
                    continue

                payload = {
                    'bugzilla_id' : bug.bugzilla_id,
                    'analysis' : sync.on_bugzilla,
                    'payload' : bug.payload,
                    'payload_hash' : bug.payload_hash,
                }

                # Send payload to server
                try:
                    self.make_request('post', '/bugs', json.dumps(payload))
                    logger.info('Added bug #{} on analysis {}'.format(bugzilla_id, ', '.join(map(str, sync.on_bugzilla))))
                except Exception as e:
                    logger.error('Failed to add bug #{} : {}'.format(bugzilla_id, e))

            elif len(sync.on_remote) > 0:
                # Remove bugs from remote server
                try:
                    self.make_request('delete', '/bugs/{}'.format(bugzilla_id))
                    logger.info('Deleted bug #{} from analysis {}'.format(bugzilla_id, ', '.join(map(str, sync.on_remote))))
                except Exception as e:
                    logger.warning('Failed to delete bug #{} : {}'.format(bugzilla_id, e))

@click.command('run_workflow_local', short_help='Update all analysis & related bugs, using local database.')
@with_appcontext
def run_workflow_local():
    """
    Run the full bug update workflow
    """
    bugzilla_url = os.environ.get('BUGZILLA_URL', 'https://bugzilla.mozilla.org')
    bugzilla_token = os.environ.get('BUGZILLA_TOKEN')

    workflow = WorkflowLocal(bugzilla_url, bugzilla_token)
    workflow.run()


@click.command('run_workflow', short_help='Run all analysis from a remote server. Stores on server')
@with_appcontext
def run_workflow():
    """
    Build analysis, without storing it in DB
    """
    keys = ('SHIPIT_REMOTE_URL', 'SHIPIT_BOT_ID', 'SHIPIT_BOT_TOKEN')

    def _check(key):
        v = os.environ.get(key)
        if v is None:
            raise Exception('Missing env {}'.format(key))
        return v

    bugzilla_url = os.environ.get('BUGZILLA_URL', 'https://bugzilla.mozilla.org')
    bugzilla_token = os.environ.get('BUGZILLA_TOKEN')

    workflow = WorkflowRemote(bugzilla_url, bugzilla_token, *map(_check, keys))
    workflow.run()
