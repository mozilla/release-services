Configuration
=============

Releng API Configuration should be stored in a file pointed to by the ``RELENGAPI_SETTINGS`` variable.

This is a typical Flask configuration file: a Python file from which any uppercase variables are extracted as configuration parameters.
For example::

    SQLALCHEMY_DATABASE_URIS = {
        'relengapi': 'sqlite:////var/lib/relengapi/relengapi.db',
    }
    CELERY_BROKER_URL='amqp://'
    CELERY_BACKEND='amqp'

The configuration file can contain any configuration parameter described in the configuration for

 * Flask - http://flask.pocoo.org/docs/config/
 * Celery - http://docs.celeryproject.org/en/master/configuration.html#configuration

The following sections describe the available configuration options, organized by topic.

.. toctree::

    database
    authentication
    permissions
    tokenauth
    aws
    memcached
    celery
    docs
