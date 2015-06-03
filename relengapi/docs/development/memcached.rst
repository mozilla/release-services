Using Memcached
===============

If your blueprint requires memcached support, RelengAPI can supply you with a `python-memcached <https://pypi.python.org/pypi/python-memcached>`_ connection instance based on the user's configuration.

The configuration syntax is described in :ref:`memcached-configuration`.

Getting a Client
----------------

To get the Client instance, pass the configuration value to :meth:`app.memcached.get <relengapi.lib.memcached.CacheFinder.cache`, using the result as a context manager.
For example::

    @bp.route('/bears')
    def get_bears():
        with current_app.memcached.get(current_app.config['BEAR_CACHE']) as mc:
            mc.get(..)
            ..

This usage ensures that the (non-thread-safe!) ``Cache`` instance can be safely re-used as necessary by other threads.
This minimizes the number of new memcached connections required, while ensuring instances aren't used simultaneously by multiple threads.

.. py:class:: relengapi.lib.memcached.CacheFinder

    .. py:method:: cache(config)

        :param config: configuration from :ref:`memcached-configuration`
        :returns: context manager yielding a ``memcached.Cache`` instance

        Get access to a ``memcached.Cache`` instance.

Testing and Development
-----------------------

When testing and developing a blueprint, you can use a `mock://somename` cache.
This will return an instance of `mockcache.Queue <https://pypi.python.org/pypi/mockcache/1.0.1>`_.
Later uses of the same URL in the same application will return the same Client instance.
