Utilities
=========

.. py:module: relengapi.utils

.. py:func: synchronized(lock)

    :param lock: a Lock instance

    This decorator will acquire and release the lock before and after the decorated funtion runs.
    The effect is that, for a given ``lock``, only one function decorated with ``@synchronized(lock)`` can execute at a time.

.. py:func: make_support_class(app, module_path, mechanisms, config_key, default)

    :param app: Flask app
    :param module_path: module path of caller (use ``__name__``)
    :param mechanisms: map of mechanism name to (module, class)
    :param config_key: Flask configuration key containing the configuration
    :param default: default mechanism

    This is a utility method for dynamically loading modules to implement mechanisms specified in the application configuration.
    It is used for configuration like ``RELENGAPI_ACTIONS``.
