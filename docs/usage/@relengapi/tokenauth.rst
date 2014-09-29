Token Authentication
====================

When systems outside of the Releng API need to perform restriction operations, they can do so using a *token*.
Tokens are opaque strings (currently implemented as JSON Web Tokens) which are provided in the Authentication header:

.. code-block:: none

    GET /some/resource HTTP/1.1
    Authentication: Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6OSwidiI6MX0.pVmY1aTyASlf24h4acVOiqNgt85mfViXDTvxLsY_qdY

Each token permits a limited set of permissions, specified when the token is issued.

Managing Tokens
---------------

Each token has a numeric ID, a description, and a set of associated permissions.
The string form of the token is only shown when the token is initially issued; thereafter it is referred to only by ID.

Those who are permitted the ``base.tokens.view`` permission can view all tokens, but not derive their string form.

Tokens can be issued via the form available from ``/tokenauth`` by those who have permission to the ``base.tokens.issue`` permission.
The selected permissions for the token must be a subset of those permissions the issuer can perform.

Tokens can be issued, revoked, looked up by string, and so on using API calls.
See the API documentation below for details.

API
---

Types
.....

.. api:autotype:: Token

Endpoints
.........

.. api:autoendpoint:: tokenauth.*

    These API calls can be used to manipulate tokens, given sufficient permissions.
