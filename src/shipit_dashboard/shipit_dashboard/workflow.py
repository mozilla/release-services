# coding=utf-8
from releng_common.db import db
from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.helpers import compute_dict_hash
from libmozdata.bugzilla import Bugzilla
from libmozdata.patchanalysis import bug_analysis
from sqlalchemy.orm.exc import NoResultFound
from flask.cli import with_appcontext
import logging
import pickle
import click
import json

logger = logging.getLogger(__name__)


class AnalysisWorkflow(object):
    """
    Update all analysis data
    """
    def __init__(self):
        self.bugs = {}

    def run_local_db(self):
        """
        Use all analysis stored on local db
        and update them directly
        """

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

    def run_taskcluster(self, name, parameters):
        """
        Build bug analysis for a specified Bugzilla query
        Used by taskcluster - no db interaction
        """

        # Get bugs from bugzilla, for all analysis
        logger.info('List bugs for {}'.format(name))
        raw_bugs = self.list_bugs(parameters)

        # Do patch analysis on bugs
        output = {
            'name' : name,
            'bugs' : [],
        }
        for raw_bug in raw_bugs.values():
            bug = self.update_bug(raw_bug, use_db=False)
            if bug:
                output['bugs'].append({
                    'bugzilla_id' : bug.bugzilla_id,
                    'payload' : bug.payload,
                    'payload_hash' : bug.payload_hash,
                })

        return json.dumps(output)

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


@click.command('run_workflow_local', short_help='Update all analysis & related bugs, using local database.')
@with_appcontext
def run_workflow_local():
    """
    Run the full bug update workflow
    """
    workflow = AnalysisWorkflow()
    workflow.run_local_db()


@click.command('run_workflow', short_help='Run analysis on a specified Bugzilla search request. Outputs on stdout, used by taskcluster.')
@click.argument('name')
@click.argument('parameters')
@with_appcontext
def run_workflow(name, parameters):
    """
    Build analysis, without storing it in DB
    """
    workflow = AnalysisWorkflow()
    print(workflow.run_taskcluster(name, parameters))
