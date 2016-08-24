from flask_login import LoginManager

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
        self.credentials = taskcluster
        self._permissions = None

    def get_id(self):
        import pdb
        pdb.set_trace()
        return 'taskcluster:%s' % self.authenticated_email

    def get_permissions(self):
        # TODO:
        import pdb
        pdb.set_trace()
        if self._permissions is not None:
            return self._permissions
        if 'perms' in session and session.get('perms_exp', 0) > time.time():
            self._permissions = set(p[perm] for perm in session['perms'])
        else:
            self._permissions = perms = set()
            permissions_stale.send(
                current_app._get_current_object(),
                user=self,
                permissions=perms)
            session['perms'] = [str(perm) for perm in perms]
            lifetime = current_app.config.get(
                'RELENGAPI_PERMISSIONS', {}).get('lifetime', 3600)
            session['perms_exp'] = int(time.time() + lifetime)
        return self._permissions


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

    @login_manager.user_loader
    def user_loader(session_identifier):
        import pdb
        pdb.set_trace()
        # TODO: load 
        try:
            typ, email = session_identifier.split(':', 1)
        except ValueError:
            return
        if typ == 'human':
            return HumanUser(email)

    @login_manager.request_loader
    def request_loader(request):

        header = request.headers.get('Authorization')
        if not header:
            return

        import pdb
        pdb.set_trace()


    login_manager.init_app(app)

    return Auth(login_manager)
