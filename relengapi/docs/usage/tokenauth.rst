.. _Token-Usage:

Token Authentication
====================

Authenticating with Tokens
--------------------------

When systems outside of the Releng API need to make API calls, they can do so using a *token*.
Tokens are opaque strings (actually JSON Web Tokens) which are provided in the Authorization header:

.. code-block:: none

    GET /some/resource HTTP/1.1
    Authorization Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6OSwidiI6MX0.pVmY1aTyASlf24h4acVOiqNgt85mfViXDTvxLsY_qdY

Each token permits a limited set of permissions, specified when the token is issued.

Issuing Tokens Via UI
---------------------

If you have adequate permissions, the API home page will display a link to manage tokens.
On this page, you can issue, examine, and revoke user and permanent tokens, depending on your permissions.

User Tokens and User Permissions
--------------------------------

User tokens which grant permissions that the user no longer posesses are automatically disabled.
In the UI, they are indicated with a "(DISABLED)" tag.
Such tokens are not usable for authentication
If the user's permissions change back (for example, if the user was misconfigured temporarily), the token will be re-enabled.

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

User Token (``usr``)
....................

A user token is issued by a non-administrative user, and lasts as long as that user's account is still active.
User tokens are very similar to GitHub's "personal access tokens" -- they entitle the bearer to act as the user, with some subset of the user's permissions.

A user token has attributes ``id``, ``permissions``, ``user``, and ``description``.
The ``user`` attribute is filled in automatically when the token is issued.
A request to issue a user token must use an authentication mechanism associated with a user (a browser session or another user token).

Temporary Token (``tmp``)
.........................

A temporary token has a limited lifetime, and can have a small amount of metadata attached.
Temporary tokens are used to give short-term, narrowly-focused permissions to other systems.
For example, a build job might use a temporary token to record its results, with the permissions of the token limited to writing results for its build ID.

A temporary token has attributes ``not_before``, ``expires``, ``permissions``, and ``metadata``.
The ``not_before`` attribute should be omitted when requesting a new token; the API will set it to the current time.

A temporary token cannot be valid beyond ``RELENGAPI_TMP_TOKEN_MAX_LIFETIME`` seconds in the future; see :ref:`Auth-Token-Config`.

Token Permissions
-----------------

Permission to manipulate tokens are controlled by a number of permissions:

For permanent tokens:
 * ``base.tokens.prm.view`` -- view all permanent tokens
 * ``base.tokens.prm.issue`` -- issue a permanent token
 * ``base.tokens.prm.revoke`` -- revoke a permanent token

For user tokens:
 * ``base.tokens.usr.view.all`` -- view all user tokens
 * ``base.tokens.usr.view.my`` -- view my user tokens
 * ``base.tokens.usr.issue`` -- issue a user token
 * ``base.tokens.usr.revoke.all`` -- revoke any user token
 * ``base.tokens.usr.revoke.my`` -- revoke a user token issued by me

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
