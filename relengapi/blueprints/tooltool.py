# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import current_app
from flask import redirect

metadata = {
    'repository_of_record': 'https://git.mozilla.org/?p=build/tooltool.git;a=summary',
    'bug_report_url': 'http://goo.gl/XZpyie',  # bugzilla saved new-bug form
}

bp = Blueprint('tooltool', __name__)


@bp.route('/sha512/<hash>')
def get(hash):
    """Fetch a link to the file with the given hash"""
    expires_in = 60
    region = 'us-east-1'
    bucket = 'mozilla-releng-use1-tooltool'
    key = '/sha512/{}'.format(hash)

    s3 = current_app.aws.connect_to('s3', region)
    signed_url = s3.generate_url(
        method='GET', expires_in=expires_in, bucket=bucket, key=key)

    return redirect(signed_url)
