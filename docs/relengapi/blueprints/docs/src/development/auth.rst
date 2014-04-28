Authentication and Authorization
================================

User Authentication
-------------------

Releng API is an API, and as such most access is limited using OAuth2, described below.
However, the setup for new OAuth2 tokens is controlled by normal, browser-based logins.

You should be familiar with the :ref:`authentication configuration <Deployment-Authentication>` documentation.

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

Authorization centers around "actions", which are a particular kind of what Flask-Principal calls "Needs".
These should be simple verbs, perhaps with an object.
Actions are fine-grained.

Each HTTP request takes place in an identity context which allows zero or more actions.
A view function can require that a particular action be permitted using a simple decorator, or use more complicated Flask-Principal functionality to make more complex permissions checks.

Each action is represented internally as a tuple of identifiers, and is usually written separated by dots.
Generally the first element corresponds to the name of the blueprint the action applies to.
For example, an identity context might have the "tasks.create" action to create tasks, handled by the tasks blueprint.

Accessing Actions
.................

A bit of syntactic sugar makes it very easy to access actions ::

    from relengapi.principal import actions
    r = actions.tasks.view

The ``actions`` object generates actions through attribute access, so the example above creates the ``tasks.view`` action.

Adding Actions
..............

To add a new action, simply access it and document it with the  :py:meth:`~relengapi.lib.actions.Action.doc` method::

    from relengapi import actions
    actions.tasks.view.doc("View tasks")

Verifying an Action
...................

Actions that aren't documented can't be used.
The :py:meth:`~relengapi.lib.actions.Action.exists` method verifies that it can be used.

Requiring a Action
..................

To protect a view function, use the action's  :py:meth:`~relengapi.lib.actions.Action.require` method as a decorator, *below* the route decorator::

    @bp.route('/observate')
    @actions.tasks.view.require()
    def view():
        ..

For more complex needs, follow the Flask-Principal documentation.
For example, to allow either of two actions::

    view_or_cancel = Permission(
        actions.tasks.view,
        actions.tasks.cancel)

    @route('/view')
    @view_or_cancel.require()
    def view():
        ..

The Action class
................

.. py:class:: relengapi.lib.actions.Action

    .. py:method:: doc(doc)

        :param doc: documentation for the action

        Set the documentation string for an action

    .. py:method:: exists()

        Verify that this action exists (is documented)

    .. py:method:: require()

        Return a decorator for view functions that will require this permission, and fail with a 403 response if permission is not granted.
        The return value is the same as that from Flask-Principal's ``Permission.request`` method, so it can also be used as a context manager.

    .. py:method:: __str__()

        Return the dot-separated string representation of this action.

.. py:class:: relengapi.lib.actions.Actions

    There is exactly one instance of this class, at ``relengapi.actions``.

    .. py:method:: __getitem__(index):

        :param index: string representation of an action
        :returns: Action

        Return the named action if, and only if, it already exists.

    .. py:method:: get(index, default=None)

        :param index: string representation of an action
        :param default: default value if ``index`` is not found
        :returns: Action or default

        Return the named action if it already exists, otherwise return the default
