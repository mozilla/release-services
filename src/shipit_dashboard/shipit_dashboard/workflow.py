# coding=utf-8
from releng_common.db import db
from shipit_dashboard.models import BugAnalysis, BugResult
from shipit_dashboard.helpers import compute_dict_hash
from clouseau.bugzilla import Bugzilla
from clouseau.patchanalysis import bug_analysis
from sqlalchemy.orm.exc import NoResultFound
from flask.cli import with_appcontext
import logging
import pickle
import click

logger = logging.getLogger(__name__)


class AnalysisWorkflow(object):
    """
    Update all analysis data
    """
    def __init__(self):
        self.bugs = {}

    def run(self):
        """
        Main workflow enty point
        """

        all_analysis = BugAnalysis.query.all()
        for analysis in all_analysis:

            # Get bugs from bugzilla, for all analysis
            raw_bugs = self.list_bugs(analysis)

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

    def list_bugs(self, analysis):
        """
        List all the bugs in an analysis
        """
        assert isinstance(analysis, BugAnalysis)
        assert analysis.parameters is not None

        logger.info('List bugs for {}'.format(analysis))

        def _bughandler(bug, data):
            data[bug['id']] = bug

        bugs = {}
        bz = Bugzilla(analysis.parameters, bughandler=_bughandler, bugdata=bugs)
        bz.get_data().wait()

        return bugs

    def update_bug(self, bug):
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
        br.payload = pickle.dumps(payload, 2)
        br.payload_hash = bug_hash
        logger.info('Updated payload of {}'.format(br))

        # Save in local cache
        self.bugs[bug_id] = br

        return br


@click.command('run_workflow', short_help='Update all analysis & related bugs')
@with_appcontext
def run_workflow():
    """
    Run the bug update workflow
    """
    workflow = AnalysisWorkflow()
    workflow.run()
