from flask_login import LoginManager
from flask import request
import logging
import taskcluster

logger = logging.getLogger(__name__)

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

        # Extract infos
        self.clientId = self.credentials['clientId']
        self.scopes = self.credentials['scopes']

        logger.info('Init user {}'.format(self.clientId))

    def get_id(self):
        return self.clientId

    def get_permissions(self):
        return self.scopes


class Auth(object):

    def __init__(self, login_manager):
        self.login_manager = login_manager

    def require_scope(self, scope):
        self.require_login()
        import pdb
        pdb.set_trace()

    def require_login(self):
        import pdb
        pdb.set_trace()


def init_app(app):

    login_manager = LoginManager()
    login_manager.anonymous_user = AnonymousUser

    @login_manager.header_loader
    def user_loader(auth_header):

        # Get Endpoint configuration
        host, port = request.host.split(':')
        method = request.method.lower()
        resource = request.path

        # Build taskcluster payload
        payload = {
            'resource' : resource,
            'method' : method,
            'host' : host,
            'port' : int(port),
            'authorization' : auth_header,
        }

        # Auth with taskcluster
        auth = taskcluster.Auth()
        resp = auth.authenticateHawk(payload)
        if not resp.get('status') == 'auth-success':
            raise Exception('Taskcluster rejected the authentication')

        return TaskclusterUser(resp)

    login_manager.init_app(app)

    return Auth(login_manager)

