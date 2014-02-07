Authentication and Authorization
================================

User Authentication
-------------------

Releng API is an API, and as such most access is limited using OAuth2, described below.
However, the setup for new OAuth2 tokens is controlled by normal, browser-based logins.
Note that in most API requests, ``current_user`` will not be set.

Releng API uses `Flask-Login <https://flask-login.readthedocs.org>`_ to manage user identity.

The LoginManager instance is available at ``relengapi.login_manager``.

A method can be protected from access without a user login with the ``flask_login.login_required`` decorator, just as documented.

Aside from the required methods, the ``current_user`` object has the following attributes:

 * ``authenticated_email`` - the email address of this user, as vouched for by an identity provider

The LoginManager instance is extended with a ``get_user`` method, which simply invokes the user getter.

Authorization
-------------

TODO
