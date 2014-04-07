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

If ``type`` is ``browserid``, no further options are required, as browserid is a very simple protocol.
Any user will be able to authenticate. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'browserid',
    }

If ``type`` is ``proxy``, then the API trusts a plaintext header from the HTTP client to specify the username.
The header name is given in the ``header`` option, and defaults to ``"Remote-User"``.
This mode is intended for deployments where the only access to the server is from a frontend proxy which is performing authentication.
This is a common configuration with load balancers or with tools like Apache or Nginx configured using tools like ``mod_authnz_ldap``. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'proxy',
        'header': 'X-Authenticated-User',
    }

If ``type`` is ``environ``, then the API trusts an environment variable named by the ``key`` key.
This is most useful when running in ``mod_wsgi``, where other server plugins can set environment variables.
For example, ``mod_authnz_ldap`` sets ``AUTHENTICATE_*`` environment variables that can be used for this purpose. ::

    RELENGAPI_AUTHENTICATION = {
        'type': 'environ',
        'header': 'AUTHENTICATE_MAIL',
    }

Roles
.....

Once a user is authenticated, their roles must be determined.
Again, a number of mechanisms are provided, configured with the ``RELENGAPI_ROLES`` key, which is a dictionary containing options.

The ``static`` type supports a simple static mapping from user ID to roles, given in the ``roles`` key.
Roles are given as a list of strings.
For example::

    RELENGAPI_ROLES = {
        'type': 'static',
        'roles': {
            'dustin@mozilla.com': ['superhero', 'mild-mannered-reporter'],
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
