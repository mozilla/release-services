from relengapi import db
import sqlalchemy as sa
from flask import Blueprint

bp = Blueprint('clobberer', __name__)

class Builds(db.declarative_base('clobberer')):
    __tablename__ = 'builds'
    id = sa.Column(sa.Integer, primary_key=True)
    master = sa.Column(sa.String(100))
