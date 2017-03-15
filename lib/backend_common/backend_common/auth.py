from flask_login import LoginManager, current_user
from flask import request, current_app
from taskcluster.utils import scope_match
from functools import wraps
import structlog
import taskcluster


logger = structlog.get_logger('backend_common.auth')


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
        """
        Check user has some required permissions
        Using Taskcluster comparison algorithm
        """
        if len(required_permissions) > 0 \
           and not isinstance(required_permissions[0], (tuple, list)):
                required_permissions = [required_permissions]

        return scope_match(self.get_permissions(), required_permissions)

    # XXX: this should not be here

    def taskcluster_options(self):
        """
        Configure the TaskCluster Secrets client
        with optional target HAWK header
        """
        target_header = request.environ.get('HTTP_X_AUTHORIZATION_TARGET')
        if not target_header:
            raise Exception('Missing X-AUTHORIZATION-TARGET header')
        return {
            'credentials': {
                'hawkHeader': target_header
            }
        }

    def get_secret(self, name):
        """
        Helper to read a Taskcluster secret
        """
        secrets = taskcluster.Secrets(self.taskcluster_options())
        secret = secrets.get(name)
        if not secret:
            raise Exception('Missing TC secret {}'.format(name))
        return secret['secret']


class Auth(object):

    def __init__(self, anonymous_user):
        self.login_manager = LoginManager()
        self.login_manager.anonymous_user = anonymous_user
        self.app = None

    def init_app(self, app):
        self.app = app
        self.login_manager.init_app(app)

    def _require_scopes(self, scopes):
        if not self._require_login():
            return False

        with current_app.app_context():
            user_scopes = current_user.get_permissions()
            if not scope_match(user_scopes, scopes):
                diffs = [', '.join(set(s).difference(user_scopes)) for s in scopes]  # noqa
                logger.error('User {} misses some scopes: {}'.format(current_user.get_id(), ' OR '.join(diffs)))  # noqa
                return False

        return True

    def _require_login(self):
        with current_app.app_context():
            try:
                return current_user.is_authenticated
            except Exception as e:
                logger.error('Invalid authentication: {}'.format(e))
                return False

    def require_login(self, method):
        """Decorator to check if user is authenticated
        """
        @wraps(method)
        def wrapper(*args, **kwargs):
            if self._require_login():
                return method(*args, **kwargs)
        return wrapper

    def require_scopes(self, scopes):
        """Decorator to check if user has required scopes or set of scopes
        """

        assert isinstance(scopes, (tuple, list))

        if len(scopes) > 0 and not isinstance(scopes[0], (tuple, list)):
            scopes = [scopes]

        def decorator(method):
            @wraps(method)
            def wrapper(*args, **kwargs):
                logger.info('Checking scopes', scopes=scopes)
                if self._require_scopes(scopes):
                    # Validated scopes, running method
                    logger.info('Validated scopes, processing api request')
                    return method(*args, **kwargs)
                else:
                    # Abort with a 401 status code
                    return {
                        'error_title': 'Unauthorized',
                        'error_message': 'Invalid user scopes',
                    }, 401
            return wrapper
        return decorator

auth = Auth(
    anonymous_user=AnonymousUser,
)


@auth.login_manager.header_loader
def taskcluster_user_loader(auth_header):

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

        # Abort with a 401 status code
        return {
            'error_title': 'Unauthorized',
            'error_message': 'Invalid taskcluster auth.',
        }, 401

    return TaskclusterUser(resp)


def init_app(app):
    auth.init_app(app)
    return auth
