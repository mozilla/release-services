Permissions
===========

Every requeset to the Releng API takes place in an authentication context that permits some set of permissions.
Permissions are represented in the API as dot-separated strings.
For example, the ``base.tokens.issue`` permission permits the bearer to issue tokens.

Each "real" user has an associated set of permitted permissions.
See :ref:`Deployment-Permissions` to see how these permissions are configured.

Other forms of authentication, such as token authentication or OAuth, are also associated with permitted permissions.
These associtions are created dynamically when the token or OAuth credentials are issued.

When authenticated via a browser, you can see your permissions at ``/auth``.

API
---

Types
.....

.. api:autotype:: Permission

Endpoints
.........

.. api:autoendpoint:: auth.*
