Authentication and Authorization
================================

User Authentication
-------------------

Releng API is an API, and as such most access is limited using OAuth2, described below.
However, the setup for new OAuth2 tokens is controlled by normal, browser-based logins.

You should be familiar with the :doc:`authentication configuration <../deployment/auth>` documentation.

Flask-Login
...........

Releng API uses `Flask-Login <https://flask-login.readthedocs.org>`_ to manage user identity.

A method can be protected from access without a user login with the ``flask_login.login_required`` decorator, just as documented.
Flask-Login is configured to automatically redirect requests to such views to ``/userauth/login_request``, which will request a user login and redirect the user back to the original page.

Aside from the required methods, the ``current_user`` object has the following attributes:

 * ``authenticated_email`` - the email address of this user

Note that in most API requests, ``current_user`` will not be set.

BrowserID Authentication
........................

Support for BrowserID is straightforward.
The user can initiate a login by clicking the "Login" button, or by visiting ``/userauth/login_request``.
Once the login is complete, the browser makes an AJAX call to ``/userauth/login`` with the identity assertion.
The server-side code records the identity in the Flask session, and the browser reloads the page to display the login.

Similarly, the logout process involves an AJAX call to ``/userauth/logout``, which destroys the session.

External Authentication
.......................

External authentication only requires that the ``/userauth/login`` path be authenticated by the frontend.
All other paths are passed through, as they may use some other authentication mode.
This also allows users to view parts of the API without being logged in.

The login process works like this:
the "Login" button triggers an AJAX call to ``/userauth/login``.
A visit to ``/userauth/login_request`` simply redirects to ``/userauth/login``.
In either case, the login view reads the authentication information from an envirnoment variable or header as configured and sets up the Flask session.
In the case of a redirect, it then redirects the user back to the originating page.

A logout is accomplished with a similar AJAX call to ``/userauth/logout``, which desetroys the session.

Authorization
-------------

Users have different levels of access, of course.
Within the Releng API, the `Flask-Principal <https://pythonhosted.org/Flask-Principal/>`_ extension distinguishes the permissions granted to different users

Authorization centers around "roles", which are a particular kind of what Flask-Principal calls "Needs".
Each role is a tuple of identifiers, usually written separated by dots.
Generally the first element corresponds to the name of the blueprint the role corresponds to.
For example, a user might have the "tasks.observer" role to observe tasks in the tasks blueprint.

Each HTTP request takes place in the context of zero or more roles.
A view function can require a particular role using a simple decorator, or use more complicated Flask-Principal functionality to make more complex permissions checks.

Accessing Roles
...............

A bit of syntactic sugar makes it very easy to access roles::

    from relengapi.principal import roles
    r = roles.tasks.observer

The ``roles`` object generates roles through attribute access, so the example above creates the ``tasks.observer`` role.

Adding Roles
............

To add a new role, simply access it and document it::

    from relengapi.principal import roles
    roles.tasks.observer.doc("Task observer")

Roles that aren't documented can't be used.

Requiring a Role
................

To protect a view function, use the role's ``require`` method as a decorator, *below* the route decorator::

    @bp.route('/observate')
    @roles.tasks.observer.require()
    def observe():
        ..

The return value of ``require`` is the same as that from Flask-Principal's ``Permission.request`` method, so it can also be used as a context manager.

For more complex needs, follow the Flask-Principal documentation.
For example, to allow either of two roles::

    observe_or_cancel = Permission(
        roles.tasks.observer,
        roles.tasks.cancel)

    @route('/observe')
    @observe_or_cancel.require()
    def observe():
        ..
