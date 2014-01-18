from relengapi import db
from flask import Blueprint
from . import models

bp = Blueprint('base', __name__)

db.register_model(bp, 'relengapi')(models.relengapi_model)
db.register_model(bp, 'scheduler')(models.scheduler_model)
