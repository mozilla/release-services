from flask import Blueprint
from flask import jsonify
from flask import current_app

bp = Blueprint('docs', __name__)

@bp.route('/')
def root():
    rv = []
    vfs = current_app.view_functions
    for map in current_app.url_map.iter_rules():
        func = vfs[map.endpoint]
        if func.__doc__ and func.__doc__.startswith('API:'):
            rv.append((map.rule, func.__doc__))
    return jsonify(rv)
