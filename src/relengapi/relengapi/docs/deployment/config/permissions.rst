.. _Deployment-Permissions:

Permissions
===========

Once a user is authenticated, their permissions must be determined.
Again, RelengAPI provides a number of mechanisms, configured with the ``RELENGAPI_PERMISSIONS`` key, which is a dictionary containing options.

Lifetime
--------

Permissions are not queried on every request, as that can be an expensive operation.
Instead, permissions are cached for some time, and only queried when they become stale.
That cache lifetime is determined by the ``lifetime`` key, which gives the time, in seconds, to cache permissions::

    RELENGAPI_PERMISSIONS = {
        ..
        'lifetime': 3660,  # one hour (the default)
    }

Static
------

The ``static`` type supports a simple static mapping from user ID to permissions, given in the ``permissions`` key.
Permissions are given as a list of strings.
For example::

    RELENGAPI_PERMISSIONS = {
        'type': 'static',
        'permissions': {
            'dustin@mozilla.com': ['tasks.create', 'base.tokens.issue'],
        },
    }

LDAP Groups
-----------

The ``ldap-groups`` type supports looking up the authenticated user in LDAP, then mapping that user's group membership to a set of allowed permissions.
The configuration looks like this::

    RELENGAPI_PERMISSIONS = {
        'type': 'ldap-groups',

        # map from group CN to permissions
        'group-permissions': {
            'team_relops': ['tasks.create', 'base.tokens.view'],
            'team_releng': ['base.tokens.issue', 'base.tokens.view'],
            '<everyone>': ['branches.view'],
        },

        # Base LDAP URI
        'uri': "ldaps://your.ldap.server/",

        # This needs to be a user that has sufficient rights to read users and groups
        'login_dn': "<dn for bind user>",
        'login_password': "<password for bind user>",

        # The search bases for users and groups, respectively
        'user_base': 'o=users,dc=example,dc=com',
        'group_base': 'o=groups,dc=example,dc=com',

        # set this to True for extra logging
        'debug': False,
    }

Permissions are cumulative: a person has a permission if they are a member of any group configured with that permission.
In the example above, a user in both ``team_relops`` and ``team_releng`` would have permission to create tasks and to issue and view tokens.
The group name ``<everyone>`` is treated specially: it grants permission to all authenticated users, regardless of authentication mechanism.

Users must be under the subtree named by ``user_base``, and similarly groups must be under ``group_base``.
Users must have object class ``inetOrgPerson``, and groups must have object class ``groupOfNames``.


