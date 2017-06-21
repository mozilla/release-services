# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import backend_common.db
import cli_common.log
import flask
import flask_login
import functools
import itsdangerous
import sqlalchemy as sa
import taskcluster
import taskcluster.utils
import time

logger = cli_common.log.get_logger(__name__)


class BaseUser(object):

    anonymous = False
    type = None

    def __eq__(self, other):
        return isinstance(other, BaseUser) and self.get_id() == other.get_id()

    @property
    def is_authenticated(self):
        return not self.anonymous

    @property
    def is_active(self):
        return not self.anonymous

    @property
    def is_anonymous(self):
        return self.anonymous

    @property
    def permissions(self):
        return self.get_permissions()

    def get_permissions(self):
        return set()

    def get_id(self):
        raise NotImplementedError

    def __str__(self):
        return self.get_id()


class AnonymousUser(BaseUser):

    anonymous = True
    type = 'anonymous'

    def get_id(self):
        return 'anonymous:'


class TaskclusterUser(BaseUser):

    type = 'taskcluster'

    def __init__(self, credentials):
        assert isinstance(credentials, dict)
        assert 'clientId' in credentials
        assert 'scopes' in credentials
        assert isinstance(credentials['scopes'], list)

        self.credentials = credentials
        logger.info('Init user {}'.format(self.get_id()))

    def get_id(self):
        return self.credentials['clientId']

    def get_permissions(self):
        return self.credentials['scopes']

    def has_permissions(self, required_permissions):
        '''
        Check user has some required permissions
        Using Taskcluster comparison algorithm
        '''
        if len(required_permissions) > 0 \
           and not isinstance(required_permissions[0], (tuple, list)):
                required_permissions = [required_permissions]

        return taskcluster.utils.scope_match(self.get_permissions(), required_permissions)


class RelengapiTokenUser(BaseUser):

    type = 'relengapi-token'

    def __init__(self, claims, authenticated_email=None, permissions=[], token_data={}):

        self.claims = claims
        self._permissions = set(permissions)
        self.token_data = token_data

        if authenticated_email:
            self.authenticated_email = authenticated_email

    def get_id(self):
        parts = ['token', self.claims['typ']]
        if 'jti' in self.claims:
            parts.append('id={}'.format(self.claims['jti']))
        try:
            parts.append('user={}'.format(self.authenticated_email))
        except AttributeError:
            pass
        return ':'.join(parts)

    def get_permissions(self):
        return self._permissions

    def has_permissions(self, permissions):
        return all([permission in self._permissions for permission in permissions])


class Auth(object):

    def __init__(self, anonymous_user):
        self.login_manager = flask_login.LoginManager()
        self.login_manager.anonymous_user = anonymous_user
        self.app = None

    def init_app(self, app):
        self.app = app
        self.login_manager.init_app(app)

    def _require_scopes(self, scopes):
        if not self._require_login():
            return False

        with flask.current_app.app_context():
            user_scopes = flask_login.current_user.get_permissions()
            if not taskcluster.utils.scope_match(user_scopes, scopes):
                diffs = [', '.join(set(s).difference(user_scopes)) for s in scopes]  # noqa
                logger.error('User {} misses some scopes: {}'.format(flask_login.current_user.get_id(), ' OR '.join(diffs)))  # noqa
                return False

        return True

    def _require_login(self):
        with flask.current_app.app_context():
            try:
                return flask_login.current_user.is_authenticated
            except Exception as e:
                logger.error('Invalid authentication: {}'.format(e))
                return False

    def require_login(self, method):
        '''Decorator to check if user is authenticated
        '''
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            if self._require_login():
                return method(*args, **kwargs)
            return 'Unauthorized', 401
        return wrapper

    def require_scopes(self, scopes):
        '''Decorator to check if user has required scopes or set of scopes
        '''

        assert isinstance(scopes, (tuple, list))

        if len(scopes) > 0 and not isinstance(scopes[0], (tuple, list)):
            scopes = [scopes]

        def decorator(method):
            @functools.wraps(method)
            def wrapper(*args, **kwargs):
                logger.info('Checking scopes', scopes=scopes)
                if self._require_scopes(scopes):
                    # Validated scopes, running method
                    logger.info('Validated scopes, processing api request')
                    return method(*args, **kwargs)
                else:
                    # Abort with a 401 status code
                    return flask.jsonify({
                        'error_title': 'Unauthorized',
                        'error_message': 'Invalid user scopes',
                    }), 401
            return wrapper
        return decorator


auth = Auth(
    anonymous_user=AnonymousUser,
)


def jti2id(jti):
    if jti[0] != 't':
        raise TypeError('jti not in the format `t$token_id`')
    return int(jti[1:])


class RelengapiToken(backend_common.db.db.Model):
    __tablename__ = 'relengapi_auth_tokens'

    def __init__(self, permissions=None, **kwargs):
        if permissions is not None:
            kwargs['_permissions'] = ','.join((str(a) for a in permissions))
        super(RelengapiToken, self).__init__(**kwargs)

    id = sa.Column(sa.Integer, primary_key=True)
    typ = sa.Column(sa.String(4), nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    user = sa.Column(sa.Text, nullable=True)
    disabled = sa.Column(sa.Boolean, nullable=False)
    _permissions = sa.Column(sa.Text, nullable=False)

    @property
    def permissions(self):
        return [
            'project:releng:{}'.format(permission.strip().replace('.', '/'))
            for permission in self._permissions.split(',')
            if permission
        ]


@auth.login_manager.header_loader
def parse_header(auth_header):

    header = auth_header.split()
    if len(header) == 2 and header[0].lower() != 'bearer':

        TOKENAUTH_ISSUER = 'ra2'
        token_str = header[1]
        tokenauth_serializer = itsdangerous.JSONWebSignatureSerializer(flask.current_app.secret_key)

        try:
            claims = tokenauth_serializer.loads(token_str)
        except itsdangerous.BadData:
            logger.warning('Got invalid signature in token %r', token_str)
            return None
        except Exception:
            logger.exception('Error processing signature in token %r', token_str)
            return None

        # convert v1 to ra2
        if claims.get('v') == 1:
            claims = {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % claims['id']}

        if claims.get('iss') != TOKENAUTH_ISSUER:
            return

        if claims['typ'] == 'prm':
            token_id = jti2id(claims['jti'])
            token_data = RelengapiToken.query.filter_by(id=token_id).first()
            if token_data:
                assert token_data.typ == 'prm'
                return RelengapiTokenUser(claims,
                                          permissions=token_data.permissions,
                                          token_data=token_data)

        elif claims['typ'] == 'tmp':
            now = time.time()
            if now < claims['nbf'] or now > claims['exp']:
                return
            permissions = [i for i in claims['prm'] if i]
            return RelengapiTokenUser(claims, permissions=permissions)

        elif claims['typ'] == 'usr':
            token_id = jti2id(claims['jti'])
            token_data = RelengapiToken.query.filter_by(id=token_id).first()
            if token_data and not token_data.disabled:
                assert token_data.typ == 'usr'
                return RelengapiTokenUser(claims,
                                          permissions=token_data.permissions,
                                          token_data=token_data,
                                          authenticated_email=token_data.user)
        else:
            return

    # Get Endpoint configuration
    if ':' in flask.request.host:
        host, port = flask.request.host.split(':')
    else:
        host = flask.request.host
        port = flask.request.environ.get('HTTP_X_FORWARDED_PORT')
        if port is None:
            port = flask.request.scheme == 'https' and 443 or 80
    method = flask.request.method.lower()

    # Build taskcluster payload
    payload = {
        'resource': flask.request.path,
        'method': method,
        'host': host,
        'port': int(port),
        'authorization': auth_header,
    }

    # Auth with taskcluster
    auth = taskcluster.Auth()
    try:
        resp = auth.authenticateHawk(payload)
        if not resp.get('status') == 'auth-success':
            raise Exception('Taskcluster rejected the authentication')
    except Exception as e:
        logger.error('TC auth error: {}'.format(e))
        logger.error('TC auth details: {}'.format(payload))

        # Abort with a 401 status code
        return {
            'error_title': 'Unauthorized',
            'error_message': 'Invalid taskcluster auth.',
        }, 401

    return TaskclusterUser(resp)


def init_app(app):
    if app.config.get('SECRET_KEY') is None:
        raise Exception('When using `auth` extention you need to specify SECRET_KEY.')
    auth.init_app(app)
    return auth
