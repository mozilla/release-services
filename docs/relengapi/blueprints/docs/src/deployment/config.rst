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

Actions
.......

Once a user is authenticated, their permitted actions must be determined.
Again, RelengAPI provides a number of mechanisms, configured with the ``RELENGAPI_ACTIONS`` key, which is a dictionary containing options.

The ``static`` type supports a simple static mapping from user ID to actions, given in the ``actions`` key.
Roles are given as a list of strings.
For example::

    RELENGAPI_ACTIONS = {
        'type': 'static',
        'actions': {
            'dustin@mozilla.com': ['tasks.create', 'base.tokens.create'],
        },
    }

Library Configuration
---------------------

The configuration file can contain any configuration parameter specified for

 * Flask - http://flask.pocoo.org/docs/config/
 * Flask-OAuthlib - https://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
 * Celery - http://docs.celeryproject.org/en/master/configuration.html#configuration

In particular, in order to use Celery to run any tasks, you will need to set ``CELERY_BROKER_URL`` and ``CELERY_BACKEND``.

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
