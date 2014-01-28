Application Configuration
=========================

Releng API Configuration should be stored in a file pointed to by the ``RELENG_API_SETTINGS`` variable.

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

Library Configuration
---------------------

The configuration file can contain any configuration parameter specified for

 * Flask - http://flask.pocoo.org/docs/config/
 * Celery - http://docs.celeryproject.org/en/master/configuration.html#configuration

In particular, in order to use Celery to run any tasks, you will need to set ``CELERY_BROKER_URL`` and ``CELERY_BACKEND``.

Per-Blueprint Configuration
---------------------------

Each blueprint will have its own configuration variables, prefixed by the name of the blueprint.
These are described in the blueprint's own documentation.

Such configuration parameters are included in the same file.
