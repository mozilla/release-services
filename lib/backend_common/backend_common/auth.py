# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools
import time

import flask
import flask_login
import itsdangerous
import pytz
import sqlalchemy as sa
import taskcluster
import taskcluster.utils

import backend_common.db
import cli_common.log

logger = cli_common.log.get_logger(__name__)

UNAUTHORIZED_JSON = {
    'status': 401,
    'title': '401 Unauthorized: Invalid user scopes',
    'detail': 'Invalid user scopes',
    'instance': 'about:blank',
    'type': 'about:blank',
}


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

    def has_permissions(self, permissions):
        if not isinstance(permissions, (tuple, list)):
            permissions = [permissions]
        user_permissions = self.get_permissions()
        return all([
            permission in list(user_permissions)
            for permission in permissions
        ])

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

    def has_permissions(self, permissions):
        '''
        Check user has some required permissions
        Using Taskcluster comparison algorithm
        '''
        if len(permissions) > 0 \
           and not isinstance(permissions[0], (tuple, list)):
                permissions = [permissions]

        return taskcluster.utils.scopeMatch(self.get_permissions(), permissions)


class RelengapiTokenUser(BaseUser):

    type = 'relengapi-token'

    def __init__(self, claims, authenticated_email=None, permissions=[], token_data={}):

        self.claims = claims
        self._permissions = set([from_relengapi_permission(p) for p in permissions])
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
            if not taskcluster.utils.scopeMatch(user_scopes, scopes):
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
                    return flask.jsonify(UNAUTHORIZED_JSON), 401
            return wrapper
        return decorator


auth = Auth(
    anonymous_user=AnonymousUser,
)


def jti2id(jti):
    if jti[0] != 't':
        raise TypeError('jti not in the format `t$token_id`')
    return int(jti[1:])


EMPTY = object()
RELENGAPI_TOKENAUTH_ISSUER = 'ra2'
RELENGAPI_PROJECT_PERMISSION_MAPPING = {
    'tooltool/': 'releng_tooltool/',
    'base/tokens/': 'releng_tokens/',
    'mapper/': 'releng_mapper/',
}
RELENGAPI_PERMISSIONS = {
    'base.badpenny.run': 'Force a run of a badpenny task',
    'base.badpenny.view': 'See scheduled tasks and logs of previous jobs',
    'base.tokens.prm.issue': 'Issue permanent tokens',
    'base.tokens.prm.revoke': 'Revoke permanent tokens',
    'base.tokens.prm.view': 'See permanent tokens',
    'base.tokens.tmp.issue': 'Issue temporary tokens',
    'base.tokens.usr.issue': 'Issue user tokens',
    'base.tokens.usr.revoke.all': 'Revoke any user token',
    'base.tokens.usr.revoke.my': 'Revoke my user tokens',
    'base.tokens.usr.view.all': 'See all user tokens',
    'base.tokens.usr.view.my': 'See my user tokens',
    'clobberer.post.clobber': 'Submit clobber requests',
    'mapper.mapping.insert': 'Allows new hg-git mappings to be inserted into mapper db (hashes table)',
    'mapper.project.insert': 'Allows new projects to be inserted into mapper db (projects table)',
    'tooltool.download.internal': 'Download INTERNAL files from tooltool',
    'tooltool.download.public': 'Download PUBLIC files from tooltool',
    'tooltool.manage': 'Manage tooltool files, including deleting and changing visibility levels',
    'tooltool.upload.internal': 'Upload INTERNAL files to tooltool',
    'tooltool.upload.public': 'Upload PUBLIC files to tooltool'
}


def initial_data():
    user = dict()
    user['type'] = flask_login.current_user.type

    user['permissions'] = []
    for permission, permission_doc in RELENGAPI_PERMISSIONS.items():
        new_permission = from_relengapi_permission(permission)
        if flask_login.current_user.has_permissions([new_permission]):
            user['permissions'].append(dict(
                name=permission,
                doc=permission_doc,
            ))

    if getattr(flask_login.current_user, 'authenticated_email', EMPTY) != EMPTY:
        user['authenticated_email'] = flask_login.current_user.authenticated_email

    return dict(
        user=user,
        perms=RELENGAPI_PERMISSIONS,
    )


def to_relengapi_permission(_permission):
    if _permission.startswith('project:releng:services/'):
        permission = _permission[len('project:releng:services/'):]
        for prefix, project in RELENGAPI_PROJECT_PERMISSION_MAPPING.items():
            if permission.startswith(project):
                return (prefix + permission[len(project):]).replace('/', '.')
    return _permission


def from_relengapi_permission(_permission):
    permission = _permission.strip().replace('.', '/')
    for prefix, project in RELENGAPI_PROJECT_PERMISSION_MAPPING.items():
        if permission.startswith(prefix):
            return 'project:releng:services/{}{}'.format(project, permission[len(prefix):])
    return _permission


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
            from_relengapi_permission(permission)
            for permission in self._permissions.split(',')
            if permission
        ]

    def to_dict(self):
        tok = dict(
            id=self.id,
            typ=self.typ,
            description=self.description,
            permissions=[str(a) for a in self.permissions],
            disabled=self.disabled
        )
        if self.user:
            tok['user'] = self.user
        return tok


def is_relengapi_token(token_str):

    try:
        claims = flask.current_app.auth_relengapi_serializer.loads(token_str)

    except itsdangerous.BadData as e:
        logger.warning('Got invalid signature in token %r', token_str)
        logger.exception(e)
        return EMPTY

    except Exception as e:
        logger.error('Error processing signature in token %r', token_str)
        return EMPTY

    # convert v1 to ra2
    if claims.get('v') == 1:
        claims = {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % claims['id']}

    if claims.get('iss') != RELENGAPI_TOKENAUTH_ISSUER:
        return EMPTY

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
            return EMPTY
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


def claims_to_str(claims):
    assert claims['iss'] == RELENGAPI_TOKENAUTH_ISSUER
    return flask.current_app.auth_relengapi_serializer.dumps(claims).decode('utf-8')


def user_to_jsontoken(user):
    attrs = {}
    cl = user.claims
    attrs['typ'] = user.claims['typ']
    if 'nbf' in cl:
        attrs['not_before'] = datetime.datetime.utcfromtimestamp(cl['nbf']).replace(tzinfo=pytz.UTC)
    if 'exp' in cl:
        attrs['expires'] = datetime.datetime.utcfromtimestamp(cl['exp']).replace(tzinfo=pytz.UTC)
    if 'mta' in cl:
        attrs['metadata'] = cl['mta']
    if 'prm' in cl:
        attrs['permissions'] = cl['prm']

    # we never load disabled users, so this one isn't disabled
    attrs['disabled'] = False

    if user.token_data:
        td = user.token_data
        attrs['id'] = td.id
        attrs['description'] = td.description
        attrs['permissions'] = [str(p) for p in td.permissions]
        if td.user:
            attrs['user'] = td.user

    return attrs


def str_to_claims(token_str):
    try:
        claims = flask.current_app.tokenauth_serializer.loads(token_str)
    except itsdangerous.BadData:
        logger.warning('Got invalid signature in token %r', token_str)
        return None
    except Exception:
        logger.exception('Error processing signature in token %r', token_str)
        return None

    # convert v1 to ra2
    if claims.get('v') == 1:
        return {'iss': 'ra2', 'typ': 'prm', 'jti': 't%d' % claims['id']}

    if claims.get('iss') != RELENGAPI_TOKENAUTH_ISSUER:
        return None

    return claims


@auth.login_manager.request_loader
def parse_header(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        auth_header = request.headers.get('Authentication')
        if not auth_header:
            return

    if flask.current_app.config.get('CHECK_FOR_RELENGAPI_TOKEN') is True:
        header = auth_header.split()
        if len(header) == 2:
            user = is_relengapi_token(header[1])
            if user != EMPTY:
                return user

    # Get Endpoint configuration
    if ':' in request.host:
        host, port = request.host.split(':')
    else:
        host = request.host
        port = request.environ.get('HTTP_X_FORWARDED_PORT')
        if port is None:
            port = request.scheme == 'https' and 443 or 80
    method = request.method.lower()

    # Build taskcluster payload
    payload = {
        'resource': request.path,
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
        return

    return TaskclusterUser(resp)


def init_app(app):
    if app.config.get('SECRET_KEY') is None:
        raise Exception('When using `auth` extention you need to specify SECRET_KEY.')
    if app.config.get('CHECK_FOR_RELENGAPI_TOKEN') is True:
        app.auth_relengapi_serializer = itsdangerous.JSONWebSignatureSerializer(app.config.get('SECRET_KEY'))

    auth.init_app(app)
    return auth
