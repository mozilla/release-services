Actions
=======

Every requeset to the Releng API takes place in an authentication context that permits some set of actions.
Actions are represented in the API as dot-separated strings.
For example, the ``base.tokens.issue`` action permits the bearer to issue tokens.

Each "real" user has an associated set of permitted actions.
See :ref:`Deployment-Actions` to see how these actions are configured.

Other forms of authentication, such as token authentication or OAuth, are also associated with permitted actions.
These associtions are created dynamically when the token or OAuth credentials are issued.

When authenticated via a browser, you can see your permissions at ``/auth/account``.
