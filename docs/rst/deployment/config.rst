Application Configuration
=========================

Releng API Configuration should be stored in a file pointed to by the ``RELENG_API_SETTINGS`` variable.

This is a typical Flask configuration file: a Python file from which any uppercase variables are extracted as configuration parameters.
For example::

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////var/lib/relengapi/relengapi.db'

Per-Blueprint Configuration
---------------------------

Each blueprint will have its own configuration variables, prefixed by the name of the blueprint.
These are described in the blueprint's own documentation.

Such configuration parameters are included in the same file.

Global Configuration
--------------------

Aside from Flask's `built-in configuration parameters <http://flask.pocoo.org/docs/config/>`_, Releng API supports the options described here.

Databases
.........

Releng API uses Flask-SQLAlchemy to access databases, so all of the options described in `Flask-SQLAlchemy <http://pythonhosted.org/Flask-SQLAlchemy/config.html>`_ are available.

The required configuration items are:

* ``SQLALCHEMY_DATABASE_URI`` - the SQLAlchemy database URI for the "main" Releng API database

* ``SQLALCHEMY_BINDS`` - a dictionary of SQLAlchemy URIs for other, external databases that the API may use.
  The available dictionary keys are for the "common" databases:

  * ``scheduler`` - the Buildbot scheduler DB
  * ``status`` - the Buildbot status DB

  Blueprints may require additional bind URIs.
