Utilities
=========

.. py:module: relengapi.utils

.. py:func: synchronized(lock)

    :param lock: a Lock instance

    This decorator will acquire and release the lock before and after the decorated funtion runs.
    The effect is that, for a given ``lock``, only one function decorated with ``@synchronized(lock)`` can execute at a time.
