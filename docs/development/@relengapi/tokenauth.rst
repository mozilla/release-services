Token Authentication
====================

Aside from the usual browser-based cookie sessions, RelengAPI has a very flexible token-based authentication mechanism, implemented by the ``tokenauth`` blueprint.

Tokens come in the form of `JSON Web Tokens <http://self-issued.info/docs/draft-ietf-oauth-json-web-token.html>`_ in JWS format, signed by the application's secret.
Each token has a type.
The token types are summarized here:

=============== ======== =========================== ========= ========= ======================
Name            Type     Permissions                 Duration  Revokable Notes
=============== ======== =========================== ========= ========= ======================
permanent token ``prm``  perms granted to token      unlimited yes
--------------- -------- --------------------------- --------- --------- ----------------------
temporary token ``tmp``  perms granted to token      limited   no
--------------- -------- --------------------------- --------- --------- ----------------------
user token      ``usr``  intersection of user's      unlimited yes       user must be valid
                         authz perms and token perms
=============== ======== =========================== ========= ========= ======================

When a token is used to authenticate a request, the Flask ``current_user`` is a ``TokenUser`` instance with a ``claims`` attribute containing the token's JWT claims.
After verifying that ``current_user.type`` is ``token``, it is safe to rely on any of the values in ``current_user.claim``.
If the token type is linked to a user, then ``current_user.authenticated_email`` will be set to that user's email address.
If the token type is not linked to a user, then this attribute does not exist (it is not just set to ``None``).

Every token has these claims:

 * ``typ`` -- the token type as given in the table above
 * ``iss`` -- always ``ra2`` for this token scheme

The remaining claims vary by type, and are defined as follows.
For limited-duration, non-revokable tokens:

 * ``nbf`` -- "not-before" time in seconds since the epoch
 * ``exp`` -- expiration time in seconds since the epoch
 * ``mta`` -- arbitrary token metadata to limit the scope of the permissions

For unlimited-duration, revokable tokens:

 * ``jti`` -- token identifier; typically ``"t"`` plus the token ID, but subject to change
 * ``sub``
   * for app-linked tokens (``ucli``, and ``pcli``), the client identifier; typically ``c`` plus the client id, but subject to change
