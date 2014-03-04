# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Blueprint
from flask import session
from flask import redirect
from flask import render_template
from flask import g
from flask import url_for
from flask import request
from flask import jsonify
from flask import current_app
from flask_login import current_user
from flask_login import login_required
from relengapi import db
from relengapi import oauth
from relengapi import login_manager
from werkzeug.security import gen_salt
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from datetime import datetime
from datetime import timedelta


bp = Blueprint('oauth', __name__, template_folder='templates')

class Client(db.declarative_base('relengapi')):
    __tablename__ = 'oauth2_clients'

    client_id = sa.Column(sa.String(40), primary_key=True)
    client_secret = sa.Column(sa.String(55), nullable=False)

    _redirect_uris = sa.Column(sa.Text)
    _default_scopes = sa.Column(sa.Text)

    @property
    def client_type(self):
        return 'confidential'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(db.declarative_base('relengapi')):
    __tablename__ = 'oauth2_grants'

    id = sa.Column(sa.Integer, primary_key=True)

    user_email = sa.Column(sa.String(255), nullable=False)

    client_id = sa.Column(
        sa.String(40), sa.ForeignKey('oauth2_clients.client_id'),
        nullable=False,
    )
    client = relationship('Client')

    code = sa.Column(sa.String(255), index=True, nullable=False)

    redirect_uri = sa.Column(sa.String(255))
    expires = sa.Column(sa.DateTime)

    _scopes = sa.Column(sa.Text)

    def delete(self):
        current_app.db.session['relengapi'].delete(self)
        current_app.db.session['relengapi'].commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def user(self):
        return login_manager.get_user(self.user_email)


class Token(db.declarative_base('relengapi')):
    __tablename__ = 'oauth2_tokens'

    id = sa.Column(sa.Integer, primary_key=True)
    client_id = sa.Column(
        sa.String(40), sa.ForeignKey('oauth2_clients.client_id'),
        nullable=False,
    )
    client = relationship('Client')

    user_email = sa.Column(sa.String(255), nullable=False)

    # currently only bearer is supported
    token_type = sa.Column(sa.String(40))

    access_token = sa.Column(sa.String(255), unique=True)
    refresh_token = sa.Column(sa.String(255), unique=True)
    expires = sa.Column(sa.DateTime)
    _scopes = sa.Column(sa.Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def user(self):
        return login_manager.get_user(self.user_email)


@oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user_email=current_user.authenticated_email,
        expires=expires
    )
    g.db.session['relengapi'].add(grant)
    g.db.session['relengapi'].commit()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.query.filter_by(
        client_id=request.client.client_id,
        user_email=request.user.authenticated_email
    )
    # make sure that every client has only one token connected to a user
    for t in toks:
        g.db.session['relengapi'].delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_email=request.user.authenticated_email,
    )
    g.db.session['relengapi'].add(tok)
    g.db.session['relengapi'].commit()
    return tok


# TODO: temporary
@bp.route('/', methods=('GET',))
@login_required
def home():
    print session
    return render_template('home.html')


@bp.route('/client')
def client():
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    item = Client(
        client_id=client_id,
        client_secret=client_secret,
        _redirect_uris='http://euclid.r.igoro.us:8000/authorized',
        _default_scopes='email',
    )
    g.db.session['relengapi'].add(item)
    g.db.session['relengapi'].commit()
    return jsonify(
        client_id=client_id,
        client_secret=client_secret,
    )


@bp.route('/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        kwargs['client'] = g.db.session['relengapi'].query(Client).filter_by(client_id=client_id).first()
        return render_template('oauthorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@bp.route('/token')
@oauth.token_handler
def access_token():
    return None


@bp.route('/secret')
@oauth.require_oauth('email')
def secret(oareq):
    return jsonify(secret='42')
