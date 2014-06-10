# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from relengapi.lib import api
from flask import Blueprint

bp = Blueprint('skel', __name__)

@bp.route('/')
@api.apimethod()
def hello():
    return {'message': 'hello world'}
