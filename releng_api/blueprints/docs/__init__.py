from flask import Blueprint

bp = Blueprint('docs', __name__)

@bp.route('/')
def root():
    return "HELLO"
