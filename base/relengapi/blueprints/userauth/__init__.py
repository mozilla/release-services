from flask import Blueprint
from flask import session
from flask import redirect
from flask import render_template
from flask import g
from flask import url_for
from flask import request
from flask import jsonify
from flask import current_app
from relengapi import db
from relengapi import login_manager
from relengapi import browser_id
from werkzeug.security import gen_salt
import sqlalchemy as sa
from flask.ext.login import UserMixin
from flask.ext.login import current_user
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import timedelta


bp = Blueprint('userauth', __name__, template_folder='templates')

# configure the login manager
login_manager.login_view = 'userauth.login_request'
login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
login_manager.get_user = lambda user_id: login_manager.user_callback(user_id)

class User(UserMixin):

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return unicode(self.authenticated_email)

@login_manager.user_loader
def login_manager_user_loader(authenticated_email):
    return User(authenticated_email)

@browser_id.user_loader
def browser_id_user_loader(login_info):
    if login_info['status'] != 'okay':
        return None
    return User(login_info['email'])
