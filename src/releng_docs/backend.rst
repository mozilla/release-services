.. _backend_docs:

``lib/backend_common``
----------------------

Service structure:

- code is located in ``src/<service>``

- ``settings.py`` - configuration for Flask application

- ``<service>/__init__.py`` -  this is where ``app`` (aka Flask app) should be
  present

- ``<service>/api.py|api.yml`` - connexion stuff (needs api extra)


Extensions
^^^^^^^^^^

TODO: what is the purpose of this

extensions:

- api

- auth

- auth0

- cache

- cors

- db

  TODO: example

- log: logbook + structlog + sentry

- pulse

- security

