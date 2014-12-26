Flask App
=========

The RelengAPI Flask App is mostly a normal Flask App, but has a few additional attributes that may be of use:

.. py:class:: Flask

    .. py:attribute:: relengapi_blueprints

        This attribute gives a list of all RelengAPI blueprints.
        It is different from ``current_app.blueprints`` in that it does not include blueprints from Flask extensions.
        Each RelengAPI blueprint has a ``dist`` attribute giving the SetupTools distribution from which the blueprint came.

    .. py:attribute:: db

        See :doc:`databases`

    .. py:attribute:: aws

        See :doc:`aws`
