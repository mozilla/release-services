from relengapi import db
import sqlalchemy as sa
from flask import Blueprint

bp = Blueprint('clobberer', __name__)

@db.register_model(bp, 'clobberer')
def model(metadata):
    sa.Table('builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('master', sa.String(100)),
    )
    sa.Table('more_builds', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('master', sa.String(100)),
    )
