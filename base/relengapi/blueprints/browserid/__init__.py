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
from werkzeug.security import gen_salt
import sqlalchemy as sa
from flask.ext.login import UserMixin
from flask.ext.login import login_user
from flask.ext.login import logout_user
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import timedelta


bp = Blueprint('browserid', __name__, template_folder='templates')

# configure the login manager
login_manager.login_view = 'browserid.login'
login_manager.logout_view = 'browserid.logout'
login_manager.login_message = 'Please authenticate to the Releng API before proceeding'
login_manager.get_user = lambda user_id: login_manager.user_callback(user_id)

@login_manager.user_loader
class User(UserMixin):

    def __init__(self, authenticated_email):
        self.authenticated_email = authenticated_email

    def get_id(self):
        return unicode(self.authenticated_email)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        login_user(User(email))
        return redirect(request.args.get('next') or url_for('root'))
    return render_template('login.html')


@bp.route('/logout', methods=('GET', 'POST'))
def logout():
    logout_user()
    return redirect(url_for('root'))

