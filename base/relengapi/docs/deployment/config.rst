Application Configuration
=========================

Releng API Configuration should be stored in a file pointed to by the ``RELENGAPI_SETTINGS`` variable.

This is a typical Flask configuration file: a Python file from which any uppercase variables are extracted as configuration parameters.
For example::

    SQLALCHEMY_DATABASE_URIS = {
        'relengapi': 'sqlite:////var/lib/relengapi/relengapi.db',
    }
    CELERY_BROKER_URL='amqp://'
    CELERY_BACKEND='amqp'

Base Configuration
------------------

Databases
.........

Releng API, as a kind of glue, generally connects to a numnber of databases.
Each database has a short name, and requires that a longer SQLAlchemy URL be configured for it.

This is done in the ``SQLALCHEMY_DATABASE_URIS`` configuration, which is a dictionary mapping names to URLs.

The databases for the base blueprint are

  * ``relengapi`` - the Releng API's own DB
  * ``scheduler`` - the Buildbot scheduler DB
  * ``status`` - the Buildbot status DB

Other blueprints may require additional bind URIs.

.. _Deployment-Authentication:

Authentication
..............

Releng API supports a number of authentication mechanisms.
These are configured with the ``RELENGAPI_AUTHENTICATION`` key, which is a dictionary containing options.
The only required option is ``type``, which specifies the authentication type.

Browserid
~~~~~~~~~

If ``type`` is ``browserid``, no further options are required, as browserid is a very simple protocol.
Any user will be able to authenticate. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'browserid',
    }

External (proxy or environment)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's common to deploy webapps with authentication done by a frontend service.
In this case the app sees only the authenticated username, not the credentials used for authentication, thereby reducing the dissemination of those credentials.
The ``external`` authentication mechanism supports this.

In all cases, only the ``/userauth/login`` URL is checked for authentication.
The frontend must pass all other URLs through without requiring authentication, as they may be API calls authenticated with some other mechanism.

On success, the authentication information is cached in the Flask session.

If the ``header`` key is provided, then the API trusts a plaintext header from the HTTP client to specify the username.
This mode is intended for deployments where the only access to the server is from a frontend proxy which is performing authentication.
This is a common configuration with load balancers or with tools like Apache or Nginx configured using tools like ``mod_authnz_ldap``.
It is critical that such configuration not allow access directly to the Releng API process!  ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'external',
        'header': 'X-Authenticated-User',
    }

If ``environ`` is given, then the API trusts an environment variable named by that key.
This is most useful when running in ``mod_wsgi``, where other server plugins can set environment variables.
For example, ``mod_authnz_ldap`` sets ``AUTHENTICATE_*`` environment variables that can be used for this purpose. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'external',
        'environ': 'AUTHENTICATE_MAIL',
    }

.. _Deployment-Permissions:

Permissions
...........

Once a user is authenticated, their permissions must be determined.
Again, RelengAPI provides a number of mechanisms, configured with the ``RELENGAPI_PERMISSIONS`` key, which is a dictionary containing options.

Lifetime
~~~~~~~~

Permissions are not queried on every request, as that can be an expensive operation.
Instead, permissions are cached for some time, and only queried when they become stale.
That cache lifetime is determined by the ``lifetime`` key, which gives the time, in seconds, to cache permissions::

    RELENGAPI_PERMISSIONS = {
        ..
        'lifetime': 3660,  # one hour (the default)
    }

Static
~~~~~~

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
~~~~~~~~~~~

The ``ldap-groups`` type supports looking up the authenticated user in LDAP, then mapping that user's group membership to a set of allowed permissions.
The configuration looks like this::

    RELENGAPI_PERMISSIONS = {
        'type': 'ldap-groups',

        # map from group CN to permissions
        'group-permissions': {
            'team_relops': ['tasks.create', 'base.tokens.view'],
            'team_releng': ['base.tokens.issue', 'base.tokens.view'],
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

Users must be under the subtree named by ``user_base``, and similarly groups must be under ``group_base``.
Users must have object class ``inetOrgPerson``, and groups must have object class ``groupOfNames``.

Library Configuration
---------------------

The configuration file can contain any configuration parameter specified for

 * Flask - http://flask.pocoo.org/docs/config/
 * Celery - http://docs.celeryproject.org/en/master/configuration.html#configuration

Celery
......

In order to use Celery to run any tasks, you will need to set ``CELERY_BROKER_URL`` and ``CELERY_BACKEND``:

.. code-block:: none

    CELERY_BROKER_URL='amqp://'
    CELERY_BACKEND='amqp'

Celery currently defaults to using pickle to serialize messages, yet complains that this is deprecated.
To avoid these warnings, use JSON instead:

.. code-block:: none

    CELERY_ACCEPT_CONTENT=['json']
    CELERY_TASK_SERIALIZER='json'
    CELERY_RESULT_SERIALIZER='json'

Documentation Configuration
---------------------------

The ``relengapi-docs`` package builds documentation from reStructuredText files, and must write the built HTML somewhere in this process.
By default, this is a sibling directory to the documentation source, but in a production environment that directory may not be writeable.
To customize the location, set ``DOCS_BUILD_DIR``.

Per-Blueprint Configuration
---------------------------

Each blueprint will have its own configuration variables, prefixed by the name of the blueprint.
These are described in the blueprint's own documentation.

Such configuration parameters are included in the same file.
