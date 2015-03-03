# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import redirect

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__)


@bp.route('/sha512/<hash>')
def get(hash):
    """Fetch a link to the file with the given hash"""
    return redirect("http://tooltool.pvt.build.mozilla.org/build/sha512/" + hash)
