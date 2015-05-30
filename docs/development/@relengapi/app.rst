Flask App
=========

The RelengAPI Flask App is mostly a normal Flask App, but has a few additional attributes that may be of use:

.. py:class:: flask.Flask

    .. py:attribute:: authz

        Access to authorization functionality outside of a request context.
        See :doc:`auth`.

    .. py:attribute:: aws

        Amazon Web Services functionality.
        See :doc:`aws`.

    .. py:attribute:: celery

        A [Celery](http://www.celeryproject.org/) app -- for internal use.
        See :doc:`tasks`.

    .. py:attribute:: db

        Database access.
        See :doc:`databases`.

    .. py:attribute:: layout

        Control of the global Jinja2 layout.
        See :doc:`web-ui`.

    .. py:attribute:: memcached

        Access to configured memcached caches.
        See :doc:`memcached`

    .. py:attribute:: relengapi_blueprints

        This attribute gives a list of all RelengAPI blueprints.
        It is different from ``current_app.blueprints`` in that it does not include blueprints from Flask extensions.
        Each RelengAPI blueprint has a ``dist`` attribute giving the SetupTools distribution from which the blueprint came.


Blueprints can add their own attributes to the application as necessary.
These should generally begin with the name of the blueprint to avoid name collisions.
