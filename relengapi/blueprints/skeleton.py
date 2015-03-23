# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from relengapi.lib import api

bp = Blueprint('skeleton', __name__)


@bp.route('/')
@api.apimethod({unicode: unicode})
def hello():
    return {'message': 'hello world'}

metadata = {
    # 'repository_of_record': '..'
    # 'bug_report_url': '..',
}
