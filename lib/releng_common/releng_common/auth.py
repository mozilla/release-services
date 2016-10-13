from flask_login import LoginManager, current_user
from flask import request, abort, current_app
from taskcluster.utils import scope_match
from functools import wraps
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

        logger.info('Init user {}'.format(self.get_id()))

    def get_id(self):
        return self.credentials['clientId']

    def get_permissions(self):
        return self.credentials['scopes']

    def taskcluster_secrets(self):
        """
        Configure the TaskCluster Secrets client
        with optional target HAWK header
        """
        target_header = request.environ.get('HTTP_X_AUTHORIZATION_TARGET')
        if not target_header:
            raise Exception('Missing X-AUTHORIZATION-TARGET header')

        options = {
            'credentials' : {
                'hawkHeader' : target_header
            }
        }
        return taskcluster.Secrets(options)

    def get_secret(self, name):
        """
        Helper to read a Taskcluster secret
        """
        secrets = self.taskcluster_secrets()
        secret = secrets.get(name)
        if not secret:
            raise Exception('Missing TC secret {}'.format(name))
        return secret['secret']


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


def scopes_required(scopes):
    """
    Decorator for Flask views to require
    some Taskcluster scopes for the current user
    """
    assert isinstance(scopes, list)

    def decorator(method):
        @wraps(method)
        def decorated_function(*args, **kwargs):
            with current_app.app_context():
                # Check login
                if not current_user.is_authenticated:
                    logger.error('Invalid authentication')
                    return abort(401)

                # Check scopes, using TC implementation
                user_scopes = current_user.get_permissions()
                if not scope_match(user_scopes, scopes):
                    diffs = [', '.join(set(s).difference(user_scopes)) for s in scopes]
                    logger.error('User {} misses some scopes: {}'.format(current_user.get_id(), ' OR '.join(diffs)))
                    return abort(401)

            return method(*args, **kwargs)
        return decorated_function
    return decorator

def init_app(app):

    login_manager = LoginManager()
    login_manager.anonymous_user = AnonymousUser

    @login_manager.header_loader
    def user_loader(auth_header):

        # Get Endpoint configuration
        if ':' in request.host:
            host, port = request.host.split(':')
        else:
            host = request.host
            port = request.environ.get('HTTP_X_FORWARDED_PORT')
            if port is None:
                request.scheme == 'https' and 443 or 80
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
        try:
            resp = auth.authenticateHawk(payload)
            if not resp.get('status') == 'auth-success':
                raise Exception('Taskcluster rejected the authentication')
        except Exception as e:
            logger.error('TC auth error: {}'.format(e))
            logger.error('TC auth details: {}'.format(payload))
            abort(401) # Unauthorized

        return TaskclusterUser(resp)

    login_manager.init_app(app)

    return Auth(login_manager)
