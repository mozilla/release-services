Authentication and Authorization
================================

Releng API is an API, and as such most access is to API endpoints, often authenticated with something other than a session cookie.
However, the API also has a normal, browser-based UI used to manage permissions, view documentation, and so on.

You should be familiar with the :ref:`authentication configuration <Deployment-Authentication>` documentation and with `Flask-Login <https://flask-login.readthedocs.org>`_.

User Objects
------------

A request to the Releng API may be authenticated in a variety of ways -- not just by the usual session cookie.
Some of these are not associated with a real, human user.

The ``flask.ext.login.current_user`` object, then, may be one of several subclassses of :class:`relenapi.lib.auth.BaseUser` corresponding to the type of authentication performed.
Each has a ``type`` attribute identifying the authentication type.
This list is extensible, but the built-in options are:

 * ``"anonymous"`` - no authentication at all
 * ``"human"`` - a human, session-based login, with additional attributes:
    * ``authenticated_email`` - the email address of this human user

Casting a user object to a string will generate a string with the pattern ``type:identifier`` that can be used for logging, messaging, etc.

Decorating Methods
------------------

A method can be protected from anonymous access with the ``flask_login.login_required`` decorator, just as documented.
Flask-Login is configured to automatically redirect requests to such views to ``/login_request``, which will request that the user login and redirect the user back to the original page.

Human Authentication Mechanisms
-------------------------------

Authentication mechanisms are implemented as setuptools plugins.
Each mechanism's ``init_app`` method is listed in the ``relengapi.auth.mechanisms`` entry point group.
During application initialization, the mechanism selected by the app configuration is loaded and initialized.

The built-in mechanisms are described here:

BrowserID Authentication
~~~~~~~~~~~~~~~~~~~~~~~~

Support for BrowserID is straightforward.
The user can initiate a login by clicking the "Login" button.
Once the login is complete, the browser makes an AJAX call to ``/userauth/login`` with the identity assertion.
The server-side code records the identity in the Flask session, and the browser reloads the page to display the login.

Similarly, the logout process involves an AJAX call to ``/userauth/logout``, which destroys the session.

External Authentication
~~~~~~~~~~~~~~~~~~~~~~~

External authentication only requires that the ``/userauth/login`` path be authenticated by the frontend.
All other paths must be passed through, as they may use some other authentication mode.
This also allows users to view parts of the API without being logged in.

The login process works like this: the "Login" button triggers an AJAX call to ``/userauth/login``.
The login view reads the authentication information from an envirnoment variable or header as configured and sets up the Flask session.

A logout is accomplished with a similar AJAX call to ``/userauth/logout``, which destroys the session.

Request Authentication
----------------------

Non-human authentication is handled by processing requests directly.
Functions to perform such processing should be registered using :func:`relengapi.lib.auth.request_loader`.
The registered function will be called once for each request, and should return a user object if the request matches.
In most cases, this object will be a purpose-specific subclass of :class:`relengapi.lib.auth.BaseUser`.

A simple example::

    class LocalhostUser(auth.baseUser):
        type = "localhost"

    @auth.request_loader
    def allow_localhost(request):
        address = request.remote_addr
        if address == '127.0.0.1':
        return LocalhostUser()

This is a very low-level interface.
In most cases, you will take advantage of token authentication to handle non-browser authentication.

Token Authentication
--------------------

The ``tokenauth`` blueprint implements a request loader which looks for bearer tokens containing JSON Web Tokens.
When this authentication succeeds, the curent user is a ``TokenUser`` object, with type ``"token"``.
It has a ``claims`` attribute which contains the JWT claims in the original token.
This can be used, for example, for access to the metadata in temporary tokens.

See :doc:`tokenauth` for more detail on the implementation of token authentication.

Authorization
-------------

Users have different levels of access, of course.
Within the Releng API, the `Flask-Principal <https://pythonhosted.org/Flask-Principal/>`_ extension distinguishes the permissions granted to different users

Authorization centers around "permissions".
These are fine-grained simple verbs, qualified with a context perhaps an object.
Generally the first element corresponds to the name of the blueprint the permission applies to.
For example, a job-management blueprint might have permissions like ``jobs.view``, ``jobs.cancel.own``, ``jobs.cancel.any``, and ``jobs.submit``.

Each HTTP request takes place in an user which allows some (possibly empty!) set of permissions.
A view function can require that particular permissions be in this set using a simple decorator (:py:meth:`~relengapi.lib.permissions.require`).

Working with Permissions
~~~~~~~~~~~~~~~~~~~~~~~~

Accessing Permissions
.....................

A bit of syntactic sugar makes it very easy to access permissions ::

    from relengapi import p
    r = p.tasks.view

The ``permissions`` object generates permissions through attribute access, so the example above creates the ``tasks.view`` permission.

Adding Permissions
..................

To add a new permission, simply access it and document it with the  :py:meth:`~relengapi.lib.permissions.Permission.doc` method::

    from relengapi import p
    p.tasks.view.doc("View tasks")

Verifying a Permission
......................

Permissions that aren't documented can't be used.
The :py:meth:`~relengapi.lib.permissions.Permission.exists` method verifies that a permission can be used.

Requiring a Permission
......................

To protect a view function, use the permission's  :py:meth:`~relengapi.lib.permissions.Permission.require` method as a decorator, *below* the route decorator::

    @bp.route('/observate')
    @p.tasks.view.require()
    def view():
        ..

For more complex needs, use the :py:func:`relengapi.lib.permissions.require` function, which takes an arbitrary number of permissions and requires *all* of them::

    from relengapi.lib import permissions
    @route('/view')
    @permissions.require(permissions.tasks.view, permissions.tasks.revoke)
    def view():
        ..

Checking for Permission
.......................

Like the ``require`` method and function, :py:meth:`~relengapi.lib.permissions.Permission.can` and :py:func:`~relengapi.lib.permissions.can` allow checking whether the current user has a permission or a set of permissions.
For example::

    if p.tasks.view.can():
        ..
    elif permissions.can(p.tasks.revoke, p.tasks.view):
        ..

Permissions Plugins
~~~~~~~~~~~~~~~~~~~

Like authentication mechanisms, authorization mechanisms are implemented as setuptools plugins.
Each mechanism's ``init_app`` method is listed in the ``relengapi.auth.mechanisms`` entry point group.
During application initialization, the mechanism selected by the app configuration is loaded and initialized.
This avoids the need to even import mechanisms that aren't being used.

Human users' permissions are updated as needed (based on the ``RELENGAPI_PERMISSIONS.lifetime`` configuration), and otherwise cached in the session cookie.
When permissions need to be updated, the :py:attr:`relengapi.lib.auth.permissions_stale` signal is sent with the user object and a set of :py:class:`~relengapi.lib.permissions.Permission` objects.
Permissions plugins should connect to this signal and add additional Permissions objects to this set to grant those permissions to the given user.

The Permission class
~~~~~~~~~~~~~~~~~~~~

.. py:module:: relengapi.lib.permissions

.. py:class:: Permission

    .. py:method:: doc(doc)

        :param doc: documentation for the permission

        Set the documentation string for an permission

    .. py:method:: exists()

        Verify that this permission exists (is documented)

    .. py:method:: require()

        Return a decorator for view functions that will require this permission, and fail with a 403 response if permission is not granted.

        .. warning::

            This decorator must appear *below* the ``route`` decorator for each view function!

    .. py:method:: can()

        Return True if the current user can perform this permission.

    .. py:method:: __str__()

        Return the dot-separated string representation of this permission.

.. py:class:: Permissions

    There is exactly one instance of this class, at ``relengapi.p``.

    .. py:method:: __getitem__(index):

        :param index: string representation of an permission
        :returns: Permission

        Return the named permission if, and only if, it already exists.

    .. py:method:: get(index, default=None)

        :param index: string representation of an permission
        :param default: default value if ``index`` is not found
        :returns: Permission or default

        Return the named permission if it already exists, otherwise return the default

.. py:function:: require(*permissions)

    Return a decorator for view functions that will require all of the given permissions;
    See :py:meth:`Permission.require`.

.. py:function:: can(*permissions)

    Return True if the current user can perform all of the given permissions
    See :py:meth:`Permission.can`.

Out-of-band Authorization Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For cases where you need information about a user outside of a request context for that user, use ``app.authz``.

The Flask application has an ``authz`` attribute that is a subclass of this class:

.. py:class:: relengapi.lib.auth.base.BaseAuthz

    .. py:method:: get_user_permissions(email)

        :param email: user's email
        :raises: NotImplementedError
        :returns: set of permissions or None

        Get the given user's permissions, or None if the user is not available.

