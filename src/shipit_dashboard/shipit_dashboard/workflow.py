# coding=utf-8
from releng_common.db import db
from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.helpers import compute_dict_hash
from shipit_dashboard.encoder import ShipitJSONEncoder
from libmozdata.bugzilla import Bugzilla
from libmozdata.patchanalysis import bug_analysis
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


class Workflow(object):
    """
    Update all analysis data
    """
    def __init__(self):
        self.bugs = {}

    def run(self):
        raise NotImplementedError

    def list_bugs(self, query):
        """
        List all the bugs from a Bugzilla query
        """
        def _bughandler(bug, data):
            data[bug['id']] = bug

        bugs = {}
        bz = Bugzilla(query, bughandler=_bughandler, bugdata=bugs)
        bz.get_data().wait()

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

        payload = {
            'bug': bug,
            'analysis': analysis,
        }
        br.payload = use_db and pickle.dumps(payload, 2) or payload
        br.payload_hash = bug_hash
        logger.info('Updated payload of {}'.format(br))

        # Save in local cache
        self.bugs[bug_id] = br

        return br

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
            analysis.bugs[:] = []
            db.session.commit()

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
    def __init__(self, api_url, client_id, access_token, *args, **kwargs):
        super(WorkflowRemote, self).__init__(*args, **kwargs)
        self.api_url = api_url
        self.credentials = {
          'id' : client_id,
          'key' : access_token,
          'algorithm' : 'sha256',
        }

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
            logger.info('List bugs for {}'.format(analysis['name']))

            # Get bugs from bugzilla, for each analysis
            raw_bugs = self.list_bugs(analysis['parameters'])

            for raw_bug in raw_bugs.values():
                # Do patch analysis on bugs
                bug = self.update_bug(raw_bug, use_db=False)
                if not bug:
                    continue
                payload = {
                    'bugzilla_id' : bug.bugzilla_id,
                    'analysis' : [ analysis['id'] ], # TODO: detect multiple analysis
                    'payload' : bug.payload,
                    'payload_hash' : bug.payload_hash,
                }

                # Send payload to server
                self.make_request('post', '/bugs', json.dumps(payload))


@click.command('run_workflow_local', short_help='Update all analysis & related bugs, using local database.')
@with_appcontext
def run_workflow_local():
    """
    Run the full bug update workflow
    """
    workflow = WorkflowLocal()
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

    workflow = WorkflowRemote(*map(_check, keys))
    workflow.run()
