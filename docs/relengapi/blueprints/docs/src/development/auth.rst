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

TODO

Note that in most API requests, ``current_user`` will not be set.
