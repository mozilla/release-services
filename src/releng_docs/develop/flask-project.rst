.. _develop-flask-project:

Flask project
=============

- Every backend project is also a python project. Make sure you read everything
  about python project (TODO: link) since everything applies also for backend
  projects.
  
- Backend projects has a ``create_app`` method in ``src/<project>/__init__.py``
  module. ``create_app`` method accepts one argument ``config``, which is later
  passed to ``backend_common.create_app``. ``create_app`` method returns an
  flask application object which is created using ``backend_common.create_app``
  helper method, eg:

  .. code-block:: python

      import backend_common

      def create_app(config=None):
          bac

- Deployment will look for an ``app`` object in ``<project>.flask`` module and
  for this reason you need to create ``flask.py`` module, which uses
  ``create_app`` from previous section, eg:

  .. code-block:: python

      import <project>

      app = <project>.create_app()

- Flask applications are configured using ``settings.py`` file.

  ``src/<project>/settings.py`` - configuration for Flask application

- ``<service>/__init__.py`` -  this is where ``app`` (aka Flask app) should be
  present

- ``<service>/api.py|api.yml`` - connexion stuff (needs api extra)

- testing backend applications


Extensions
----------

Backend extensions are simple glue code of a recognized flask pattern (TODO:
link) that describes how to extend flask application.

The purpose of extensions is to

Extentions are always loaded in order which is defined in ``EXTENTIONS``
variable in ``lib/backend_common/backend_common/__init__.py``.

Current extensions are:

- **api**: Provides a well defined way how to create JSON API backend servies
  by integrating connexion_ python package.

  ``app.api.register`` is a helper method to let you register Swagger/OpenAPI
  specifications. eg:
  
  .. code-block:: python
      
      def create_app(config=None):
          app = backend_common.create_app(...)
          app.api.register(os.path.join(os.path.dirname(__file__), 'api.yml'))
          return app

- auth
- auth0
- cache
- cors
- db
- log:
- pulse
- security
- templates


Create new extension
--------------------

- Create a python in ``lib/backend_common/backend_common/<extension_name>.py``

- If extra dependencies are needed create an extra with extension name in
  ``lib/backend_common/setup.py``. Look for ``EXTRAS`` variable.

- Extention needs to implement ``init_app`` method which accepts one argument
  ``app`` (flask application object). The ``init_app`` method must return an
  extention object, which can be then accessed in any backend application via
  ``app.<extension_name>``.

  Example for cache extention:

  .. code-block:: python

    import flask_cache

    cache = flask_cache.Cache()

    def init_app(app):
        # read cache configuration from flask configuration and provide sane
        # defaults
        cache_config = app.config.get(
            'CACHE',
            {'CACHE_TYPE': 'simple'},
        )
        cache.init_app(app, config=cache_config)
        return cache

- Add the extention name of the file (without the ``.py``) extention to the
  ``EXTENTIONS`` list in ``lib/backend_common/backend_common/__init__.py``


.. _connexion: https://github.com/zalando/connexion
