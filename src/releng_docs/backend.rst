.. _backend_docs:


Backend project structure:

- project code is located in ``src/<project>``

  Look at contribution guide (TODO:link) how to start working on a project.

- runtime dependencies (install_requires) are listed in
  ``src/<project>/requirements.txt``

- buildtime dependencies (tests_require) are listed in 
  ``src/<project>/requirements-dev.txt``

- like every python project also our project has a ``src/<project>/setup.py``

  Use ``requirements.txt`` and ``requirements-dev.txt`` to list dependencies.
  That way we only change

  Every time you add/remove/update dependencies rereun::

      % ./please update-dependencies <project>

  More information about updating dependencies you can find here (TODO: link)


- your python module should be names the same as the project, that means that
  the code for your  python module will be located in
  ``src/<project>/<project>/``

- every flask 

  ``src/<project>/settings.py`` - configuration for Flask application

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

