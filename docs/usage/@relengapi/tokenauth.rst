Token Authentication
====================

Authenticating with Tokens
--------------------------

When systems outside of the Releng API need to make API calls, they can do so using a *token*.
Tokens are opaque strings (actually JSON Web Tokens) which are provided in the Authentication header:

.. code-block:: none

    GET /some/resource HTTP/1.1
    Authentication: Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6OSwidiI6MX0.pVmY1aTyASlf24h4acVOiqNgt85mfViXDTvxLsY_qdY

Each token permits a limited set of permissions, specified when the token is issued.

Managing Tokens
---------------

In order to issue a new token, the caller must have the appropriate issuing permission (see below) as well as all permissions in the requested token.
The string form of the token is only produced when the token is initially issued; thereafter it is referred to only by ID, if at all.

Some tokens do not have IDs.
These tokens cannot be managed after they are issued.
Fortunately, all such tokens have limited lifetimes.

Token Types
-----------

There are several types of tokens available.
Depending on your permissions, some or all of these may be unavailable to you.

To issue a token, supply all of the required attributes except ``id``.

Permanent Token (``prm``)
.........................

A permanent token is issued by an administrator and never expires -- even if that administrator's account is terminated.
Permannent tokens are used for authentication of other, internal systems to RelengAPI.

A permanent token has attributes ``id``, ``permissions``, and ``description``.

Temporary Token (``tmp``)
.........................

A temporary token has a limited lifetime, and can have a small amount of metadata attached.
Temporary tokens are used to give short-term, narrowly-focused permissions to other systems.
For example, a build job might use a temporary token to record its results, with the permissions of the token limited to writing results for its build ID.

A temporary token has attributes ``not_before``, ``expires``, ``permissions``, and ``metadata``.

Token Permissions
-----------------

Permission to manipulate tokens are controlled by a number of permissions:

For permanent tokens:
 * ``base.tokens.prm.view`` -- view all permanent tokens
 * ``base.tokens.prm.issue`` -- issue a permanent token
 * ``base.tokens.prm.revoke`` -- revoke a permanent token

For temporary tokens:
 * ``base.tokens.tmp.issue`` -- issue a temporary token.

API
---

Types
.....

.. api:autotype:: Token

Endpoints
.........

.. api:autoendpoint:: tokenauth.*

    These API calls can be used to manipulate tokens, given sufficient permissions.
