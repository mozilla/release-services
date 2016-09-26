# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import json

from releng_common import auth, db, create_app
from shipit_dashboard.workflow import run_workflow, run_workflow_local


DEBUG = os.environ.get('DEBUG') == 'true' or __name__ == '__main__'
HERE = os.path.dirname(os.path.abspath(__file__))
APP_SETTINGS = os.path.abspath(os.path.join(HERE, '..', 'settings.py'))

def init_app(app):

    # Register extra commands
    app.cli.add_command(run_workflow)
    app.cli.add_command(run_workflow_local)

    # Register swagger api
    return app.api.register(
        os.path.join(os.path.dirname(__file__), 'swagger.yml'))


def init_analysis(app):
    """
    Load initial analysis
    """
    from shipit_dashboard.models import BugAnalysis
    all_analysis = json.load(open(os.path.join(HERE, 'analysis.json'), 'r'))
    with app.app_context():
        existing = [a.name for a in BugAnalysis.query.all()]
        for name, parameters in all_analysis.items():
            if name in existing:
                continue

            # Create new analysis
            analysis = BugAnalysis(name)
            analysis.parameters = parameters
            app.db.session.add(analysis)
            app.db.session.commit()


if not os.environ.get('APP_SETTINGS') and \
       os.path.isfile(APP_SETTINGS):
    os.environ['APP_SETTINGS'] = APP_SETTINGS


app = create_app(
    "shipit_dashboard",
    extensions=[init_app, db, auth],
    debug=DEBUG,
    debug_src=HERE,
)

# Init analysis, post app creation
init_analysis(app)

if __name__ == "__main__":
    app.run(**app.run_options())
